'''
See COPYRIGHT.md for copyright information.
'''
import os, json
import regex as re
from decimal import Decimal
from collections import defaultdict, OrderedDict
from arelle.FileSource import openFileStream, openFileSource, saveFile # only needed if building a cached file
from arelle.ModelValue import qname, dateTime, DATE
from arelle import XbrlConst, UrlUtil
from arelle.PythonUtil import attrdict, flattenSequence, pyObjectSize, OrderedSet
from arelle.ValidateXbrlCalcs import inferredDecimals, floatINF
from arelle.XmlValidateConst import VALID
from .Consts import standardNamespacesPattern, latestTaxonomyDocs, latestEntireUgt, attachmentDocumentTypeValidationRulesFiles, feeTaggingAttachmentDocumentTypePattern

EMPTY_DICT = {}
EMPTY_SET = set()

def conflictClassFromNamespace(namespaceURI):
    match = standardNamespacesPattern.match(namespaceURI or "")
    if match:
        _class = match.group(2) or match.group(6)[:4] # trim ifrs-full to ifrs
        if _class.startswith("ifrs"):
            _class = "ifrs"
        return "{}/{}".format(_class, match.group(3) or match.group(5))

WITHYEAR = 0
WILD = 1
NOYEAR = 2
WITHYEARandWILD = 3
def abbreviatedNamespace(namespaceURI, pattern=WITHYEAR):
    if pattern == WITHYEARandWILD:
        return (abbreviatedNamespace(namespaceURI,WITHYEAR), abbreviatedNamespace(namespaceURI,WILD))
    match = standardNamespacesPattern.match(namespaceURI or "")
    if match:
        return {WITHYEAR: "{}/{}", WILD: "{}/*", NOYEAR: "{}"
                }[pattern].format(match.group(2) or match.group(6), match.group(3) or match.group(5))
    return None

def getEffectiveAuthority(url: str) -> str:
    # the effective authority of a URI consists of the last part of the URI between the // 
    # and the first / and containing at most one dot.
    if url:
        if url.lower().startswith("urn:"):
            # UrlUtil.authority does not handle urn well
            # effective authority for a urn is the NID
            # part between the first 2 colons
            return url.split(":")[1]
        authority = UrlUtil.authority(url, includeScheme=False)
        return ".".join(authority.split(".")[-2:])
    return url

def usgaapYear(modelXbrl):
    for d in modelXbrl.urlDocs.values():
        abbrNs = abbreviatedNamespace(d.targetNamespace)
        if abbrNs and abbrNs.startswith("us-gaap/"):
            return abbrNs[8:]
    return ""


def loadNonNegativeFacts(modelXbrl, dqcRules, ugtRels):
    # for us-gaap newer than 2020 use DQCRT non-negative facts.
    if dqcRules and ugtRels: # not used for us-gaap before 2020
        return None # use all available DQCRT tests
    # for us-gaap < 2020 use EFM non-negative warning  instead of DQCRT rules
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "signwarnings.json"), 'rt', encoding='utf-8')
    signwarnings = json.load(_file) # {localName: date, ...}
    _file.close()
    concepts = set()
    excludedMembers = set()
    excludedMemberStrings = set()
    excludedAxesMembers = defaultdict(set)
    for modelDocument in modelXbrl.urlDocs.values():
        ns = modelDocument.targetNamespace # set up non neg lookup by full NS
        for abbrNs in (abbreviatedNamespace(ns), abbreviatedNamespace(ns, WILD)):
            nsMatch = False
            for exName, exSet, isQName in (("conceptNames", concepts, True),
                                           ("excludedMemberNames", excludedMembers, True),
                                           ("excludedMemberStrings", excludedMemberStrings, False)):
                for localName in signwarnings[exName].get(abbrNs, ()):
                    exSet.add(qname(ns, localName) if isQName else localName)
                    nsMatch = True
            for localDimName, localMemNames in signwarnings["excludedAxesMembers"].get(abbrNs, EMPTY_DICT).items():
                for localMemName in localMemNames:
                    excludedAxesMembers[qname(ns, localDimName)].add(qname(ns, localMemName) if localMemName != "*" else "*")
                    nsMatch = True
            if nsMatch:
                break # use explicit year rules if available, else generic year rules
    return attrdict(concepts=concepts,
                    excludedAxesMembers=excludedAxesMembers,
                    excludedMembers=excludedMembers,
                    excludedMemberNamesPattern=re.compile("|".join(excludedMemberStrings), re.IGNORECASE)
                                               if excludedMemberStrings else None)

def loadCustomAxesReplacements(modelXbrl): # returns match expression, standard patterns
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "axiswarnings.json"), 'rt', encoding='utf-8')
    axiswarnings = json.load(_file) # {localName: date, ...}
    _file.close()
    standardAxes = {}
    matchPattern = []
    for i, (standardAxis, customAxisPattern) in enumerate(axiswarnings.items()):
        if standardAxis not in ("#", "copyright", "description"):
            patternName = "_{}".format(i)
            standardAxes[patternName] = standardAxis
            matchPattern.append("(?P<{}>^{}$)".format(patternName, customAxisPattern))
    return attrdict(standardAxes=standardAxes,
                    customNamePatterns=re.compile("|".join(matchPattern)))

class ValueRange:
    def inRange(self, v):
        return self.v1 <= v <= self.v2
    def __repr__(self):
        return f"from {self.v1} to {self.v2}"

class NumericRange(ValueRange):
    def __init__(self, r):
        self.v1 = Decimal(r[0])
        self.v2 = Decimal(r[1])

class DateRange(ValueRange):
    def __init__(self, r):
        self.v1 = dateTime(r[0], type=DATE)
        self.v2 = dateTime(r[1], type=DATE)

def loadDeiValidations(modelXbrl, isInlineXbrl, attachmentDocumentType):
    validationRulesFile = None
    hasAttachmentDocumentTypeRules = False # non-dei exhibit specific rules
    for (pattern, validationRulesFilename) in attachmentDocumentTypeValidationRulesFiles:
        if pattern is not None and pattern.match(attachmentDocumentType or ""):
            hasAttachmentDocumentTypeRules = True # non-dei exhibit type
            break
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, validationRulesFilename), 'rt', encoding='utf-8')
    validations = json.load(_file) # {localName: date, ...}
    _file.close()
    #print ("original validations size {}".format(pyObjectSize(validations)))
    prefixedNamespaces = validations["prefixed-namespaces"] = modelXbrl.prefixedNamespaces
    # set dei namespaceURI as default
    for doc in modelXbrl.urlDocs.values():
         if doc.targetNamespace and doc.targetNamespace.startswith("http://xbrl.sec.gov/dei/"):
             prefixedNamespaces[None] = doc.targetNamespace
             break
    # compile sub-type-classes
    stc = validations["sub-type-classes"]
    def compileSubTypeSet(forms, formSet=None, visitedClasses=None):
        if visitedClasses is None: visitedClasses = set()
        if formSet is None: formSet = OrderedSet()
        for form in flattenSequence(forms):
            if form.startswith("@"):
                referencedClass = form[1:]
                if referencedClass not in stc:
                    modelXbrl.error("arelle:loadDeiValidations", _("Missing declaration for %(referencedClass)s."), referencedClass=form)
                elif form in visitedClasses:
                    modelXbrl.error("arelle:loadDeiValidations",
                                    _("Circular reference to %(formClass)s in %(formClasses)s."),
                                    formClass=referencedClass, formClasses=sorted(visitedClasses))
                else:
                    visitedClasses.add(form)
                    compileSubTypeSet(stc[referencedClass], formSet, visitedClasses)
            else:
                formSet.add(form)
        return formSet
    for sev in validations["sub-type-element-validations"]:
        if all(k.startswith("comment") for k in sev.keys()):
            continue
        for field in (
            ("xbrl-names",) if "store-db-name" in sev else
            ("xbrl-names", "validation") if hasAttachmentDocumentTypeRules else
            ("xbrl-names", "validation", "efm" if not "msgSection" in sev else "msgSection", "source")):
            if field not in sev:
                modelXbrl.error("arelle:loadDeiValidations",
                                _("Missing sub-type-element-validation[\"%(field)s\"] from %(validation)s."),
                                field=field, validation=sev)
            elif field == "msgSection":
                pattern = re.compile(r".*:\d+(\.\d+)*")
                if not pattern.match(sev[field]):
                    modelXbrl.error("arelle:loadDeiValidations",
                                    _("Invalid format for \"%(field)s\" in %(validation)s. Value \"%(value)s\" does not match regex \"%(pattern)s\"."),
                                    field=field, validation=sev, value=sev[field], pattern=pattern.pattern)
        if "severity" in sev and not any(field.startswith("message") for field in sev) and not hasAttachmentDocumentTypeRules:
            modelXbrl.error("arelle:loadDeiValidations",
                            _("Missing sub-type-element-validation[\"%(field)s\"] from %(validation)s."),
                            field="message*", validation=sev)
        validationCode = sev.get("validation")
        if validationCode in ("f2", "og", "ol1", "ol2", "oph", "ar", "sr", "oth", "t", "tb", "t1", "te") and "references" not in sev:
            modelXbrl.error("arelle:loadDeiValidations",
                            _("Missing sub-type-element-validation[\"references\"] from %(validation)s."),
                            field=field, validation=sev)
        if validationCode in ("ru", "ou"):
            if isinstance(sev.get("value"), list):
                sev["value"] = set(sev["value"]) # change options list into set
            else:
                modelXbrl.error("arelle:loadDeiValidations",
                                _("Missing sub-type-element-validation[\"value\"] from %(validation)s, must be a list."),
                                field=field, validation=sev)
        if validationCode and validationCode.startswith("fdep") and "references"not in sev:
            modelXbrl.error("arelle:loadDeiValidations",
                            _("Missing sub-type-element-validation[\"references\"] from %(validation)s."),
                            field=field, validation=sev)
        if validationCode in ():
            if isinstance(sev.get("reference-value"), list):
                sev["reference-value"] = set(sev["reference-value"]) # change options list into set
            else:
                modelXbrl.error("arelle:loadDeiValidations",
                                _("Missing sub-type-element-validation[\"value\"] from %(validation)s, must be a list."),
                                field=field, validation=sev)
        if not validationCode and "store-db-name" in sev:
            sev["validation"] = None # only storing, no validation
        elif validationCode not in validations["validations"]:
            modelXbrl.error("arelle:loadDeiValidations", _("Missing validation[\"%(validationCode)s\"]."), validationCode=validationCode)
        axisCode = sev.get("axis")
        if axisCode and axisCode not in validations["axis-validations"]:
            modelXbrl.error("arelle:loadDeiValidations", _("Missing axis[\"%(axisCode)s\"]."), axisCode=axisCode)
        if "lang" in sev:
            sev["langPattern"] = re.compile(sev["lang"])
        s = sev.get("source")
        if s is None and not validationCode and "store-db-name" in sev and not hasAttachmentDocumentTypeRules:
            pass # not a validation entry
        elif s not in ("inline", "non-inline", "both") and not hasAttachmentDocumentTypeRules:
            modelXbrl.error("arelle:loadDeiValidations", _("Invalid source [\"%(source)s\"]."), source=s)
        elif (isInlineXbrl and s in ("inline", "both")) or (not isInlineXbrl and s in ("non-inline", "both")) or (not s and hasAttachmentDocumentTypeRules):
            messageKey = sev.get("message")
            if messageKey and messageKey not in validations["messages"]:
                modelXbrl.error("arelle:loadDeiValidations", _("Missing message[\"%(messageKey)s\"]."), messageKey=messageKey)
            # only include dei names in current dei taxonomy
            sev["xbrl-names"] = [name
                                 for name in flattenSequence(sev.get("xbrl-names", ()))
                                 if qname(name, prefixedNamespaces) in modelXbrl.qnameConcepts or name.endswith(":*") or name.startswith("header:")]
            if "references" in sev:
                sev["references"] = flattenSequence(sev["references"])
                if "reference-value" not in sev:
                    sev["reference-value"] = ["!not!", "absent"] # default condition
            subTypeSet = compileSubTypeSet(sev.get("sub-types", (sev.get("sub-type",()),)))
            if "*" in subTypeSet:
                subTypeSet = {"all"} # change to string for faster testing in Filing.py
            sev["subTypeSet"] = subTypeSet
            if "sub-types-pattern" in sev:
                sev["subTypesPattern"] = re.compile(sev["sub-types-pattern"])
            sev["formTypeSet"] = compileSubTypeSet(sev.get("form-types", (sev.get("form-type",()),)))

        # allow value to be a list which includes @ references to sub types
        for valueKey in ("value", "reference-value", "store-db-valid-values"):
            if valueKey in sev and isinstance(sev[valueKey],list) and any(e.startswith("@") for e in sev[valueKey] if isinstance(e,str)):
                sev[valueKey] = compileSubTypeSet(sev[valueKey])
        if "value-pattern" in sev:
            sev["value"] = re.compile(sev["value-pattern"])
        if "value-date-range" in sev:
            sev["value"] = DateRange(sev["value-date-range"])
        if "value-numeric-range" in sev:
            sev["value"] = NumericRange(sev["value-numeric-range"])
        # check where predicates, must be lists
        for field, value in sev.items():
            if field.endswith("where") and isinstance(value, dict):
                for cond, clause in value.items():
                    if not isinstance(clause, list):
                        modelXbrl.error("arelle:loadDeiValidations",
                                        _("Where clause %(field)s %(cond)s from %(validation)s, must be a list."),
                                        field=field, cond=cond, validation=sev)
                    else:
                        if any(e.startswith("@") for e in clause if isinstance(e,str)):
                            value[cond] = list(compileSubTypeSet(clause)) # where clause needs to keep order and be subscriptable
            if field.endswith("value-map") and isinstance(value, str):
                if not value.startswith("@"):
                        modelXbrl.error("arelle:loadDeiValidations",
                                        _("%(field)s %(cond)s from %(validation)s, must be a dictionary or a reference to a dictionary."),
                                        field=field, cond=value, validation=sev)
                referencedClass = value[1:]
                if referencedClass not in stc:
                    modelXbrl.error("arelle:loadDeiValidations", _("Missing declaration for %(referencedClass)s."), referencedClass=value)
                else:
                    sev[field] = stc[referencedClass]
                                        
    for axisKey, axisValidation in validations["axis-validations"].items():
        messageKey = axisValidation.get("message")
        if messageKey and messageKey not in validations["messages"]:
            modelXbrl.error("arelle:loadDeiValidations", _("Missing axis \"%(axisKey)s\" message[\"%(messageKey)s\"]."),
                            axisKey=axisKey, messageKey=messageKey)
    for valKey, validation in validations["validations"].items():
        messageKey = validation.get("message")
        if messageKey and messageKey not in validations["messages"]:
            modelXbrl.error("arelle:loadDeiValidations", _("Missing validation \"%(valKey)s\" message[\"%(messageKey)s\"]."),
                            valKey=valKey, messageKey=messageKey)

#print ("compiled validations size {}".format(pyObjectSize(validations)))
    return validations

def loadTaxonomyCompatibility(modelXbrl):
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "taxonomy-compatibility.json"), 'rt', encoding='utf-8')
    compat = json.load(_file, object_pairs_hook=OrderedDict) # preserve order of keys
    _file.close()
    tc = compat["taxonomy-classes"]
    cc = compat["compatible-classes"]
    def refTx(txAbbrs):
        return [refTx(tc[txAbbr[1:]]) if txAbbr.startswith("@") else txAbbr
                for txAbbr in txAbbrs
                ] if isinstance(txAbbrs, list) else []
    for k in cc.keys():
        cc[k] = set(flattenSequence(refTx(cc[k])))
    compat["checked-taxonomies"] = set(flattenSequence([t for t in cc.items()]))
    return compat

def loadIxTransformRegistries(modelXbrl):
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "ixbrl-transform-registries.json"), 'rt', encoding='utf-8')
    ixTrRegistries = json.load(_file, object_pairs_hook=OrderedDict) # preserve order of keys
    _file.close()
    ixTrRegistries.pop("copyright", None)
    ixTrRegistries.pop("description", None)
    return ixTrRegistries


def loadDeprecatedConceptDates(val, deprecatedConceptDates):
    for modelDocument in val.modelXbrl.urlDocs.values():
        ns = modelDocument.targetNamespace
        abbrNs = abbreviatedNamespace(ns, WILD)
        if abbrNs in latestTaxonomyDocs:
            latestTaxonomyDoc = latestTaxonomyDocs[abbrNs]
            _fileName = deprecatedConceptDatesFile(val.modelXbrl.modelManager, abbrNs, latestTaxonomyDoc)
            if _fileName:
                _file = openFileStream(val.modelXbrl.modelManager.cntlr, _fileName, 'rt', encoding='utf-8')
                _deprecatedConceptDates = json.load(_file) # {localName: date, ...}
                _file.close()
                for localName, date in _deprecatedConceptDates.items():
                    deprecatedConceptDates[qname(ns, localName)] = date

def resourcesFilePath(modelManager, *paths):
    # resourcesDir can be in cache dir (production) or in validate/EFM/resources (for development)
    _resourcesDir = os.path.join( os.path.dirname(__file__), "resources") # dev/testing location
    _target = "validate/EFM/resources"
    if not os.path.isabs(_resourcesDir):
        _resourcesDir = os.path.abspath(_resourcesDir)
    if not os.path.exists(_resourcesDir): # production location
        _resourcesDir = os.path.join(modelManager.cntlr.webCache.cacheDir, "resources", "validation", "EFM")
        _target = "web-cache/resources"
    return os.path.join(_resourcesDir, *paths)

def deprecatedConceptDatesFile(modelManager, abbrNs, latestTaxonomyDoc):
    cntlr = modelManager.cntlr
    _fileName = resourcesFilePath(modelManager, abbrNs.partition("/")[0] + "-deprecated-concepts.json")
    _deprecatedLabelRolePattern = re.compile(latestTaxonomyDoc["deprecatedLabelRolePattern"])
    _deprecatedDateMatchPattern = latestTaxonomyDoc["deprecationDatePattern"]
    if os.path.exists(_fileName):
        return _fileName
    # load labels and store file name
    modelManager.addToLog(_("loading {} deprecated concepts into {}").format(abbrNs, _fileName), messageCode="info")
    deprecatedConceptDates = {}
    from arelle import ModelXbrl
    for latestTaxonomyLabelFile in flattenSequence(latestTaxonomyDoc["deprecatedLabels"]):
        # load without SEC/EFM validation (doc file would not be acceptable)
        priorValidateDisclosureSystem = modelManager.validateDisclosureSystem
        modelManager.validateDisclosureSystem = False
        deprecationsInstance = ModelXbrl.load(modelManager,
              # "http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-doc-2012-01-31.xml",
              # load from zip (especially after caching) is incredibly faster
              openFileSource(latestTaxonomyLabelFile, cntlr),
              _("built deprecations table in cache"))
        modelManager.validateDisclosureSystem = priorValidateDisclosureSystem
        if deprecationsInstance is None:
            modelManager.addToLog(
                _("%(name)s documentation not loaded"),
                messageCode="arelle:notLoaded", messageArgs={"modelXbrl": val, "name":_abbrNs})
        else:
            # load deprecations
            for labelRel in deprecationsInstance.relationshipSet(XbrlConst.conceptLabel).modelRelationships:
                modelLabel = labelRel.toModelObject
                conceptName = labelRel.fromModelObject.name
                if _deprecatedLabelRolePattern.match(modelLabel.role or ""):
                    match = _deprecatedDateMatchPattern.match(modelLabel.text)
                    if match is not None:
                        date = match.group(1)
                        if date:
                            deprecatedConceptDates[conceptName] = date

            jsonStr = json.dumps(
                OrderedDict(((k, v) for k, v in sorted(deprecatedConceptDates.items()))),  # sort in json file
                            ensure_ascii=False, indent=0)
            saveFile(cntlr, _fileName, jsonStr)
            deprecationsInstance.close()
            del deprecationsInstance # dereference closed modelXbrl

def buildDeprecatedConceptDatesFiles(cntlr):
    # will build in subdirectory "resources" if exists, otherwise in cache/resources
    for abbrNs, latestTaxonomyDoc in latestTaxonomyDocs.items():
        if latestTaxonomyDoc is not None and abbrNs and abbrNs != "invest/*":
            # don't rebuild invest, use static file of all entries
            deprecatedConceptDatesFile(cntlr.modelManager, abbrNs, latestTaxonomyDoc)

def loadOtherStandardTaxonomies(modelXbrl, val):
    _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "other-standard-taxonomies.json"), 'rt', encoding='utf-8')
    otherStandardTaxonomies = json.load(_file) # {localName: date, ...}
    _file.close()
    otherStandardNsPrefixes = otherStandardTaxonomies.get("taxonomyPrefixes",{})
    return set(doc.targetNamespace
               for doc in modelXbrl.urlDocs.values()
               if doc.targetNamespace and
               doc.targetNamespace not in val.disclosureSystem.standardTaxonomiesDict
               and any(doc.targetNamespace.startswith(nsPrefix) for nsPrefix in otherStandardNsPrefixes))

def loadUgtRelQnames(modelXbrl, dqcRules):
    if not dqcRules:
        return {} # not a us-gaap filing
    disclosureSystem = modelXbrl.modelManager.disclosureSystem
    abbrNs = ""
    for modelDocument in modelXbrl.urlDocs.values():
        abbrNs = abbreviatedNamespace(modelDocument.targetNamespace)
        if abbrNs and abbrNs.startswith("us-gaap/"):
            break
    if not abbrNs: # no gaap/ifrs taxonomy for this filing
        return {}
    _ugtRelsFileName = resourcesFilePath(modelXbrl.modelManager, "us-gaap-rels-{}.json".format(abbrNs.rpartition("/")[2]))
    if not os.path.exists(_ugtRelsFileName):
        buildUgtFullRelsFiles(modelXbrl, dqcRules)
    if not os.path.exists(_ugtRelsFileName):
        return {}
    _file = openFileStream(modelXbrl.modelManager.cntlr, _ugtRelsFileName, 'rt', encoding='utf-8')
    ugtRels = json.load(_file) # {localName: date, ...}
    _file.close()
    def qn(nsPrefix, localName):
        return qname(nsPrefix + ":" + localName, modelXbrl.prefixedNamespaces)
    ugtCalcsByQnames = defaultdict(dict) # store as concept indices to avoid using memory for repetitive strings
    for wgt, fromNSes in ugtRels["calcs"].items():
        calcWgtObj = ugtCalcsByQnames.setdefault(float(wgt), {}) # json weight object needs to be float
        for fromNs, fromObjs in fromNSes.items():
            for fromName,toNSes in fromObjs.items():
                fromConcept = modelXbrl.qnameConcepts.get(qn(fromNs, fromName))
                if fromConcept is not None:
                    calcFromObj = calcWgtObj.setdefault(fromConcept.qname,set())
                    for toNs, toNames in toNSes.items():
                        for toName in toNames:
                            toConcept = modelXbrl.qnameConcepts.get(qn(toNs, toName))
                            if toConcept is not None:
                                calcFromObj.add(toConcept.qname)
    ugtAxesByQnames = defaultdict(set) # store as concept indices to avoid using memory for repetitive strings
    for axisName, memNames in ugtRels["axes"].items():
        for axisConcept in modelXbrl.nameConcepts.get(axisName,()):
            if axisConcept.qname.namespaceURI in disclosureSystem.standardTaxonomiesDict: # ignore extension concepts
                axisObj = ugtAxesByQnames[axisConcept.name]
                for memName in memNames:
                    for memConcept in modelXbrl.nameConcepts.get(memName,()):
                        if memConcept.qname.namespaceURI in disclosureSystem.standardTaxonomiesDict: # ignore extension concepts
                            axisObj.add(memConcept.qname)
    ugtAxisDefaultQnames = {}
    for axisName, defName in ugtRels["axis-defaults"].items():
        for axisConcept in modelXbrl.nameConcepts.get(axisName,()):
            if axisConcept.qname.namespaceURI in disclosureSystem.standardTaxonomiesDict: # ignore extension concepts
                for defConcept in modelXbrl.nameConcepts.get(defName,()):
                    if defConcept.qname.namespaceURI in disclosureSystem.standardTaxonomiesDict: # ignore extension concepts
                        ugtAxisDefaultQnames[axisConcept.qname] = defConcept.qname
    ugt = {"calcs": ugtCalcsByQnames,
           "axes": ugtAxesByQnames,
           "axis-defaults": ugtAxisDefaultQnames,
           "accrual-items": set(ugtRels["accrual-items"])}
    for ugtItem in ("730000-items", "non-CF", "non-CF-abstracts1", "SHE-exceptions"):
        ugt[ugtItem] = ugtRels[ugtItem]
    # dqc0015 now uses XULE reloadable constants
    '''
    if "DQC.US.0015" in ugtRels:
        dqc0015 = ugtRels["DQC.US.0015"]
        concepts = set()
        excludedMembers = set()
        excludedMemberStrings = set()
        excludedAxesMembers = defaultdict(set)
        conceptRuleIDs = {}
        for exName, exSet, isQName in (("conceptNames", concepts, True),
                                       ("excludedMemberNames", excludedMembers, True),
                                       ("excludedMemberStrings", excludedMemberStrings, False)):
            for ns, names in dqc0015[exName].items():
                for localName in names:
                    exSet.add(qn(ns, localName) if isQName else localName)
        for localDimNs, localDimMems in dqc0015["excludedAxesMembers"].items():
            for localDimName, localMemObjs in localDimMems.items():
                for localMemNs, localMemNames in localMemObjs.items():
                    if localMemNs == "*":
                        excludedAxesMembers[qn(localDimNs, localDimName)].add("*")
                    else:
                        for localMemName in localMemNames:
                            excludedAxesMembers[qn(localDimNs, localDimName)].add(qn(localMemNs, localMemName) if localMemName != "*" else "*")
        #if abbrNs < "us-gaap/2021": # no rel ids in us-gaap/2020
        #    _ugtRelsFileName = resourcesFilePath(modelXbrl.modelManager, "us-gaap-rels-2021.json")
        #    _file = openFileStream(modelXbrl.modelManager.cntlr, _ugtRelsFileName, 'rt', encoding='utf-8')
        #    ugtRels = json.load(_file) # {localName: date, ...}
        #    _file.close()
        for conceptNs, conceptNameIDs in ugtRels["DQC.US.0015"]["conceptRuleIDs"].items():
            for conceptName, conceptID in conceptNameIDs.items():
                conceptRuleIDs[qn(conceptNs, conceptName)] = conceptID
        ugt["DQC.US.0015"] = attrdict(concepts=concepts,
                                  excludedAxesMembers=excludedAxesMembers,
                                  excludedMembers=excludedMembers,
                                  excludedMemberNamesPattern=re.compile("|".join(excludedMemberStrings), re.IGNORECASE)
                                               if excludedMemberStrings else None,
                                               conceptRuleIDs=conceptRuleIDs)
    '''
    return ugt

def addDomMems(rel, mems, useLocalName=False, baseTaxonomyOnly=False, visited=None):
    if visited is None: visited = set()
    modelXbrl = rel.modelXbrl
    disclosureSystem = modelXbrl.modelManager.disclosureSystem
    toConcept = rel.toModelObject
    if toConcept not in visited: # prevent looping
        if not baseTaxonomyOnly or toConcept.qname.namespaceURI in disclosureSystem.standardTaxonomiesDict:
            mems.add(toConcept.name if useLocalName else toConcept.qname)
        visited.add(toConcept)
        for childRel in modelXbrl.relationshipSet(XbrlConst.domainMember, rel.consecutiveLinkrole).fromModelObject(toConcept):
            addDomMems(childRel, mems, useLocalName, baseTaxonomyOnly, visited)
        visited.remove(toConcept)


def buildUgtFullRelsFiles(modelXbrl, dqcRules):
    from arelle import ModelXbrl
    modelManager = modelXbrl.modelManager
    cntlr = modelXbrl.modelManager.cntlr
    conceptRule = ("http://fasb.org/dqcrules/arcrole/concept-rule", # FASB arcrule
                   "http://fasb.org/dqcrules/arcrole/rule-concept")
    rule0015 = "http://fasb.org/us-gaap/role/dqc/0015"
    # load without SEC/EFM validation (doc file would not be acceptable)
    priorValidateDisclosureSystem = modelManager.validateDisclosureSystem
    modelManager.validateDisclosureSystem = False
    for ugtAbbr, (ugtEntireUrl, dqcrtUrl) in latestEntireUgt.items():
        modelManager.addToLog(_("loading {} Entire UGT {}").format(ugtAbbr, ugtEntireUrl), messageCode="info")
        ugtRels = {}
        ugtCalcs = {}
        ugtAxes = defaultdict(set)
        ugtAxisDefaults = {}
        accrualItems = set()
        ugtInstance = ModelXbrl.load(modelManager,
              # "http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-doc-2012-01-31.xml",
              # load from zip (especially after caching) is incredibly faster
              openFileSource(ugtEntireUrl, cntlr),
              _("built dqcrt table in cache"))
        if ugtInstance is None:
            modelManager.addToLog(
                _("%(name)s documentation not loaded"),
                messageCode="arelle:notLoaded", messageArgs={"modelXbrl": val, "name":ugtAbbr})
        else:
            # load signwarnings from DQC 0015
            calcRelSet = ugtInstance.relationshipSet(XbrlConst.summationItems)
            preRelSet = ugtInstance.relationshipSet(XbrlConst.parentChild)
            for rel in calcRelSet.modelRelationships:
                _fromQn = rel.fromModelObject.qname
                _toQn = rel.toModelObject.qname
                ugtCalcs.setdefault(rel.weight,{}).setdefault(_fromQn.prefix,{}).setdefault(_fromQn.localName,{}
                        ).setdefault(_toQn.prefix,set()).add(_toQn.localName)
            for w in ugtCalcs.values():
                for fNs in w.values():
                    for fLn in fNs.values():
                        for tNs in fLn.keys():
                            fLn[tNs] = sorted(fLn[tNs]) # change set to array for json
            dimDomRelSet = ugtInstance.relationshipSet(XbrlConst.dimensionDomain)
            axesOfInterest = set()
            for rule in dqcRules["DQC.US.0001"]["rules"].values():
                axesOfInterest.add(rule["axis"])
                for ruleAxesEntry in ("additional-axes", "unallowed-axes"):
                    for additionalAxis in rule.get(ruleAxesEntry, ()):
                        axesOfInterest.add(additionalAxis)
            for rel in dimDomRelSet.modelRelationships:
                axisConcept = rel.fromModelObject
                if axisConcept.name in axesOfInterest:
                    addDomMems(rel, ugtAxes[axisConcept.name], True)
            for axis in tuple(ugtAxes.keys()):
                ugtAxes[axis] = sorted(ugtAxes[axis]) # change set to array for json
            for rel in ugtInstance.relationshipSet(XbrlConst.dimensionDefault).modelRelationships:
                ugtAxisDefaults[rel.fromModelObject.name] = rel.toModelObject.name
            # accrual items
            def addAccrualDescendants(rel, filter, visited=None):
                if visited is None: visited = set()
                name = rel.toModelObject.name
                toModelObject = rel.toModelObject
                if ((filter == "monetary" and toModelObject.isMonetary) or
                    (filter == "non-abstract" and not toModelObject.isAbstract) or
                    (filter == "abstract" and toModelObject.isAbstract and "Abstract" in toModelObject.name) or
                    (filter == "monetary-duration" and toModelObject.isMonetary and toModelObject.periodType == "duration")):
                    accrualItems.add(name)
                if name not in visited:
                    visited.add(name)
                    for childRel in ugtInstance.relationshipSet(rel.arcrole, rel.consecutiveLinkrole).fromModelObject(toModelObject):
                        addAccrualDescendants(childRel, filter, visited)
                    visited.discard(name)
            for parentLns, relset in ((dqcRules["DQC.US.0044"]["accrual-items-calc-parents"], calcRelSet),
                                      (dqcRules["DQC.US.0044"]["accrual-items-pre-parents"], preRelSet)):
                for parentLn in parentLns:
                    for parentConcept in ugtInstance.nameConcepts[parentLn]:
                        for rel in relset.fromModelObject(parentConcept):
                            addAccrualDescendants(rel, "monetary")
            ugtRels["accrual-items"] = sorted(accrualItems) # sort set into a list
            accrualItems.clear()
            preRelSet = ugtInstance.relationshipSet(XbrlConst.parentChild, dqcRules["DQC.US.0068"]["linkrole"])
            for rootConcept in preRelSet.rootConcepts:
                for rel in preRelSet.fromModelObject(rootConcept):
                    addAccrualDescendants(rel, "non-abstract")
            ugtRels["730000-items"] = sorted(accrualItems) # sort set into a list
            preRelSet = ugtInstance.relationshipSet(XbrlConst.parentChild)
            for setName, rule in dqcRules["DQC.US.0099"]["gaap-pre-descendants"].items():
                accrualItems.clear()
                for parentLn in rule["names"]:
                    for parentConcept in ugtInstance.nameConcepts[parentLn]:
                        for rel in preRelSet.fromModelObject(parentConcept):
                            addAccrualDescendants(rel, rule["filter"])
                ugtRels[setName] = sorted(accrualItems)
            ugtRels["calcs"] = OrderedDict(sorted(ugtCalcs.items(), key=lambda i:i[0]))
            ugtRels["axes"] = OrderedDict(sorted(ugtAxes.items(), key=lambda i:i[0]))
            ugtRels["axis-defaults"] = OrderedDict(sorted(ugtAxisDefaults.items(), key=lambda i:i[0]))
            del calcRelSet, dimDomRelSet, preRelSet
            ugtInstance.close()
            del ugtInstance # dereference closed modelXbrl

            # use DQC reloadable constants instead
            '''
            if dqcrtUrl: # none for pre-2020
                modelManager.addToLog(_("loading {} DQC Rules {}").format(ugtAbbr, dqcrtUrl), messageCode="info")
                dqcrtInstance = ModelXbrl.load(modelManager,
                      # "http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-doc-2012-01-31.xml",
                      # load from zip (especially after caching) is incredibly faster
                      openFileSource(dqcrtUrl, cntlr),
                      _("built dqcrt table in cache"))
                if dqcrtInstance is None:
                    modelManager.addToLog(
                        _("%(name)s documentation not loaded"),
                        messageCode="arelle:notLoaded", messageArgs={"modelXbrl": val, "name":ugtAbbr})
                else:
                    ugtRels["DQC.US.0015"] = dqc0015 = defaultdict(dict)
                    # load DQC 0015
                    dqcRelSet = dqcrtInstance.relationshipSet(("http://fasb.org/dqcrules/arcrole/concept-rule", # FASB arcrule
                                                               "http://fasb.org/dqcrules/arcrole/rule-concept"),
                                                               "http://fasb.org/us-gaap/role/dqc/0015")
                    for dqc0015obj, headEltName in (("conceptNames", "Dqc_0015_ListOfElements"),
                                                    ("excludedMemberNames", "Dqc_0015_ExcludeNonNegMembersAbstract"),
                                                    ("excludedAxesMembers", "Dqc_0015_ExcludeNonNegAxisAbstract"),
                                                    ("excludedAxesMembers", "Dqc_0015_ExcludeNonNegAxisMembersAbstract"),
                                                    ("excludedMemberStrings", "Dqc_0015_ExcludeNonNegMemberStringsAbstract")):
                        headElts = dqcrtInstance.nameConcepts.get(headEltName,())
                        for headElt in headElts:
                            if dqc0015obj == "excludedMemberStrings":
                                for refRel in dqcrtInstance.relationshipSet(XbrlConst.conceptReference).fromModelObject(headElt):
                                    for refPart in refRel.toModelObject.iterchildren("{*}allowableSubString"):
                                        for subStr in refPart.text.split():
                                            dqc0015[dqc0015obj].setdefault("*", []).append(subStr) # applies to any namespace
                            else:
                                for ruleRel in dqcRelSet.fromModelObject(headElt):
                                    elt = ruleRel.toModelObject
                                    if dqc0015obj in ("conceptNames", "excludedMemberNames"):
                                        dqc0015[dqc0015obj].setdefault(elt.qname.prefix, []).append(elt.name)
                                    else:
                                        l = dqc0015[dqc0015obj].setdefault(elt.qname.prefix, {}).setdefault(elt.name, {})
                                        if headEltName == "Dqc_0015_ExcludeNonNegAxisAbstract":
                                            l["*"] = None
                                        else:
                                            for memRel in dqcRelSet.fromModelObject(elt):
                                                l.setdefault(memRel.toModelObject.qname.prefix, []).append(memRel.toModelObject.name)
                    dqc0015["conceptRuleIDs"] = conceptRuleIDs = {}
                    for rel in dqcrtInstance.relationshipSet(XbrlConst.conceptReference).modelRelationships:
                        if rel.toModelObject.role == "http://fasb.org/us-gaap/role/dqc/ruleID":
                            refValue = rel.toModelObject.stringValue
                            if refValue.startswith("DQC.US.0015."):
                                conceptRuleIDs.setdefault(rel.fromModelObject.qname.prefix, {})[rel.fromModelObject.name] = int(refValue.rpartition(".")[2])

                dqcrtInstance.close()
                del dqcrtInstance # dereference closed modelXbrl
                def sortDqcLists(obj):
                    if isinstance(obj, list):
                        obj.sort()
                    elif isinstance(obj, dict):
                        for objVal in obj.values():
                            sortDqcLists(objVal)
                sortDqcLists(dqc0015)
            '''
            jsonStr = json.dumps(ugtRels, ensure_ascii=False, indent=2)
            _ugtRelsFileName = resourcesFilePath(modelManager, "us-gaap-rels-{}.json".format(ugtAbbr.rpartition("/")[2]))
            saveFile(cntlr, _ugtRelsFileName, jsonStr)  # 2.7 gets unicode this way

    modelManager.validateDisclosureSystem = priorValidateDisclosureSystem

def axisMemQnames(modelXbrl, axisQname, baseTaxonomyOnly=False):
    memQnames = set()
    for dimDomRel in modelXbrl.relationshipSet(XbrlConst.dimensionDomain).fromModelObject(modelXbrl.qnameConcepts[axisQname]):
        addDomMems(dimDomRel, memQnames, False, baseTaxonomyOnly)
    return memQnames

def memChildQnames(modelXbrl, memName):
    memQnames = set()
    for memConcept in modelXbrl.nameConcepts.get(memName,()):
        for memMemRel in modelXbrl.relationshipSet(XbrlConst.domainMember).fromModelObject(memConcept):
            addDomMems(memMemRel, memQnames)
    return memQnames

def loadDqcRules(modelXbrl): # returns match expression, standard patterns
    # determine taxonomy usage by facts, must have more us-gaap facts than ifrs facts
    # (some ifrs filings may have a few us-gaap facts or us-gaap concepts loaded but are not us-gaap filings)
    namespaceUsage = {}
    for f in modelXbrl.facts:
        ns = f.qname.namespaceURI
        namespaceUsage[ns] = namespaceUsage.get(ns, 0) + 1
    numUsGaapFacts = sum(n for ns,n in namespaceUsage.items() if "us-gaap" in ns)
    numIfrsFacts = sum(n for ns,n in namespaceUsage.items() if "ifrs" in ns)
    usGaapYr = usgaapYear(modelXbrl)
    if (usGaapYr >= "2020" and # DQCRT usage begins in 2020
        # if there are both us-gaap and ifrs facts in the instance the filing might be either
        # an ifrs or a us-gaap filing.  If ifrs the FASB DQCRT rules do not apply.
        # When a filing contains both ifrs and us-gaap facts deem the filing to be us-gaap
        # when the majority of facts are us-gaap.  This appeared workable for current filings.
        # In the future a model-based approach could be used based on submission type, e.g.
        # consider primary reporting facts in main statements and dismiss facts only used
        # in notes, disclosures or parenthetically in statements.
        ((numUsGaapFacts == 0 and numIfrsFacts == 0) or (numUsGaapFacts > numIfrsFacts))):
        _file = openFileStream(modelXbrl.modelManager.cntlr, resourcesFilePath(modelXbrl.modelManager, "dqc-us-rules.json"), 'rt', encoding='utf-8')
        dqcRules = json.load(_file, object_pairs_hook=OrderedDict) # preserve order of keys
        _file.close()
        if usGaapYr >= "2020": # files only exist starting with 2023, e.g. 2020 must use 2023 constants file
            dqcRules["XULE-constants-file"] = resourcesFilePath(modelXbrl.modelManager, "xule", f"dqcrt-us-{max(usGaapYr,'2023')}-constants.json")
        return dqcRules
    return {}

def xuleReloadConstValue(obj, elt_type=None):
    # this method reproduces XuleConstant.py method reload_value
    if obj is None:
        return None
    elif isinstance(obj, str):
        if elt_type == 'qname':
            return qname(obj) # obj is a clark name
        elif elt_type == 'decimal':
            return Decimal(obj)
        return str(obj) # should be a string
    elif isinstance(obj, (float, int)):
        return obj
    elif isinstance(obj, list):
        _type = obj[0]
        if _type == "decimal" and len(obj) == 2:
            return Decimal(obj[1])
        elif _type == "qname" and len(obj) == 2:
            return qname(obj[1])
        elif _type == "network":
            return tuple(obj[1:-1])
        elif _type == "reference":
            # this is not usable, value is ModelReference which would require a PrototypeDtsObject.py PrototypeObject to be implemented
            return tuple(obj[1:-1])
        elif _type == 'dictionary':
            values = []
            for item in obj[1:]:
                values.append( tuple(xuleReloadConstValue(elt, None) for elt in item) )
            return dict(values)
        else:
            collection_elt_type = _type.split()
            collection_type = collection_elt_type[0]
            if collection_type in ('set', 'list'):
                try:
                    elt_type = _type.split()[1]
                except IndexError:
                    elt_type = None
                values = []
                for elt in obj[1:]:
                    values.append( xuleReloadConstValue(elt, elt_type) )
                if collection_type == "set":
                    return frozenset(values)
                else:
                    return tuple(values)    

def loadXuleConstantsForPythonRules(val, dqcRules):
    xuleConsts = {}
    if "XULE-constants-file" in dqcRules:
        # reload XULE constants built for XULE rule operaition
        _file = openFileStream(val.modelXbrl.modelManager.cntlr, dqcRules["XULE-constants-file"], 'rt', encoding='utf-8')
        xuleReloadableConstants = json.load(_file)
        _file.close()
        for name, obj in xuleReloadableConstants.items():
            xuleConsts[name] = xuleReloadConstValue(obj)
    return xuleConsts
    

def factBindings(modelXbrl, localNames, nils=False, factFilter=None, noAdditionalDims=False, coverPeriod=False, coverDimQnames=EMPTY_SET, coverDimNames=EMPTY_SET, absentDimNames=EMPTY_SET, alignDims=None, coverUnit=False, cube=None, cubeRelSet=None):
    bindings = defaultdict(dict)
    def addMostAccurateFactToBinding(f):
        cntx = f.context
        if (f.xValid >= VALID
            and (nils or not f.isNil)
            and (factFilter(f) if factFilter is not None else True)
            and cntx is not None
            and (not noAdditionalDims or not (cntx.qnameDims.keys() - coverDimQnames))
            and (not absentDimNames or not any(k.localName in absentDimNames for k in cntx.qnameDims.keys()))):
            if cubeRelSet:
                if not all(cubeRelSet.isRelated(cube, "descendant", dim.member, isDRS=True) for dim in cntx.qnameDims.values()):
                    return
            if alignDims:
                h = hash( (cntx.periodHash if not coverPeriod else None, frozenset(hash(dim) for qn,dim in cntx.qnameDims.items() if qn in alignDims)) )
            elif coverPeriod:
                h = cntx.dimsHash
                hper = cntx.periodHash
            elif coverDimQnames or coverDimNames:
                h = hash( (cntx.periodHash, frozenset(dim for qn,dim in cntx.qnameDims.items() if qn not in coverDimQnames and qn.localName not in coverDimNames)) )
                hCvrDims = hash( frozenset(dim for qn,dim in cntx.qnameDims.items() if qn in coverDimQnames) )
            else:
                h = cntx.contextDimAwareHash
            binding = bindings[h, f.unit.hash if (f.unit is not None and not coverUnit) else None]
            ln = f.qname.localName
            if coverPeriod and not alignDims:
                if ln not in binding:
                    binding[ln] = defaultdict(dict)
                if hper not in binding[ln] or inferredDecimals(f) > inferredDecimals(binding[ln][hper]):
                    binding[ln][hper] = f
            elif coverDimQnames or coverDimNames:
                if ln not in binding:
                    binding[ln] = defaultdict(dict)
                if hCvrDims not in binding[ln] or inferredDecimals(f) > inferredDecimals(binding[ln][hCvrDims]):
                    binding[ln][hCvrDims] = f
            else:
                if ln not in binding or inferredDecimals(f) > inferredDecimals(binding[ln]):
                    binding[ln] = f
    for ln in localNames:
        for f in modelXbrl.factsByLocalName.get(ln,()):
            addMostAccurateFactToBinding(f)
    return bindings

def leastDecimals(binding, localNames=None):
    if localNames:
        nonNilFacts = [binding[ln] for ln in localNames if not binding[ln].isNil]
    else:
        nonNilFacts = [f for f in binding if f is not None and not f.isNil] # just plain sequence of facts not in bindings
    if nonNilFacts:
        return min((inferredDecimals(f) for f in nonNilFacts))
    return floatINF

def buildFTValidationsFile(cntlr):
    from .FtValidations import FtValidations
    FTV = FtValidations(cntlr, feeTaggingAttachmentDocumentTypePattern)
    FTV.generateValidations()

def getLatestTaxonomyFamily(modelXbrl, name):
    latest_version = None
    if not modelXbrl:
        # keeping this hard coded version just for debugging purposes.
        # This plugin is called via loadFromOIM plugin so it should have
        # a modelXbrl when called.
        class taxonomyFamily:
            def __init__(self, name):
                self.family = name.lower()
                self.namespace = f"http://xbrl.sec.gov/{self.family}/2024"
                self.href = f"https://xbrl.sec.gov/{self.family}/2024/{self.family}-2024.xsd"
        latest_version = taxonomyFamily(name)
    else:
        for family in modelXbrl.modelManager.disclosureSystem.familyHrefs.get(name, []):
            prefix = family.namespace.split("/")[-2]
            if not latest_version and prefix == name.lower():
                latest_version = family
            else:
                if prefix == name.lower() and family.version > latest_version.version:
                    latest_version = family
    return latest_version
