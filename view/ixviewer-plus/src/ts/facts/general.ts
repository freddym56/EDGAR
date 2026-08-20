/* Created by staff of the U.S. Securities and Exchange Commission.ParsedUrl
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

import { ErrorsMinor } from "../errors/minor";
import { FactMap } from "../facts/map";
import { ModalsCommon } from "../modals/common";
import { ConstantsFunctions } from "../constants/functions";
import { Pagination } from "../pagination/sideBarPagination";
import { Constants } from "../constants/constants";
import { Facts } from "../facts/facts";
import { formatFactValue } from  "../modals/fact-pages";
import { SegmentArray } from "../interface/fact"

export const FactsGeneral = {
	getElementByNameContextref: (name: string, contextref: string) => {
		return document.getElementById('dynamic-xbrl-form')?.querySelector(
			'[name="' + name + '"][contextref="' + contextref + '"]');
	},

	getMenuFactByDataID: (dataId: string) => {
		return document.getElementById('facts-menu-list-pagination')?.querySelector('[data-id="' + dataId + '"]');
	},

	/**
	 * Description
	 * @info handles clickevent from fact sidebar
	 * @param {any} event:MouseEvent|KeyboardEvent|Event
	 * @param {any} element:HTMLElement
	 * @returns {any} => 
	 */
	goToInlineFact: (event: MouseEvent | KeyboardEvent | Event, element: HTMLElement) => {
		if (event instanceof KeyboardEvent && !((event).key === 'Enter' || (event).key === 'Space' || (event).key === ' '))
			return;

		const fact = FactMap.getByID(element.getAttribute('data-id') as string);
		if (!fact?.file) {
			ErrorsMinor.factNotFound();
			return;
		}

		FactMap.setIsSelected(fact.id);
		const currentInstance = Constants.getInstances.find(element => element.current);
		const currentXHTML = currentInstance?.docs.find(element => element.current);

		const afterLoad = () => {
			const tempDiv = document.createElement('div');
			tempDiv.setAttribute('id', fact.id);
			ModalsCommon.clickEvent(event, tempDiv);

			Facts.updateURLHash(fact.id);
			// element.scrollIntoView(false);
			Pagination.setSelectedFact(element, fact);
		}

		if (currentXHTML?.slug !== fact.file) {
			ConstantsFunctions.switchDoc(fact.file)
				.then(() => afterLoad());
		} else {
			afterLoad();
		}
	},

	//TODO factmap.getbyid is used a lot
	// fact in fact sidebar
	renderFactElem: (elementID: string, hidden = false): Node => {
		const factInfo = FactMap.getByID(elementID);
		const factElem = document.createDocumentFragment();

		const aElement = document.createElement('a');
		aElement.setAttribute(
			'class',
			'text-body sidebar-fact ix-focus-inset border-bottom click text-decoration-none click list-group-item list-group-item-action p-1 ps-3'
		);
		if (hidden) {
			aElement.classList.add('d-none');
		}
		aElement.setAttribute('selected-fact', `${factInfo?.isSelected}`);
		if (factInfo?.id) {
			aElement.setAttribute('data-id', factInfo?.id);
			aElement.setAttribute('data-href', factInfo?.file || "");
		}
		aElement.setAttribute('tabindex', '13');

		const conceptWrapper = document.createElement('div');
		conceptWrapper.setAttribute('class', 'd-flex w-100 justify-content-between');
		const conceptElem = document.createElement('p');
		conceptElem.setAttribute('class', 'mb-0 font-weight-bold break-word');
		conceptElem.setAttribute('data-cy', 'concept');
		const pElementContent = document.createTextNode(ConstantsFunctions.getFactLabel(factInfo?.labels || []));
		conceptElem.appendChild(pElementContent);
		const badge = FactsGeneral.getFactBadge(factInfo);
		badge.setAttribute('data-cy', 'badge');
		conceptWrapper.appendChild(conceptElem);
		conceptWrapper.appendChild(badge);

		const factWrapper = document.createElement('div');
		factWrapper.setAttribute('class', 'd-flex w-100');

		const factValElem = document.createElement('p');
		factValElem.setAttribute('class', 'mb-0');
		factValElem.setAttribute('data-cy', 'factVal');

		

	
		let factValue = factInfo?.value ?? '';
		if (factValue && factInfo?.isAmountsOnly) {
			factValue= formatFactValue(String(factValue), factInfo.decimalsVal ?? undefined)
		} else {
			factValue = factInfo?.value  || "nil";
		}

		const p3Text = factInfo?.isHTML || factInfo?.isContinued ? 'Click to see Fact.' : factValue;
		const pElement3Content = document.createTextNode(p3Text);
		factValElem.appendChild(pElement3Content);

		const factDetailButton = document.createElement('button')
		factDetailButton.setAttribute('class', 'fact-details-btn');
		
		const factDetailIcon = document.createElement('i')
		factDetailIcon.setAttribute('class', 'fas fa-info-circle detail-icon');

		factDetailButton.appendChild(factDetailIcon);
		
		factWrapper.appendChild(factValElem);
		factWrapper.appendChild(factDetailButton);

		const container = document.createElement('div')
		container.setAttribute('class', 'd-flex justify-content-between');

		const periodElem = document.createElement('p');
		periodElem.setAttribute('class', 'mb-0 lighter-text');
		periodElem.setAttribute('data-cy', 'factPeriod');
		const pElementContent2 = document.createTextNode(factInfo?.period as string);
		periodElem.appendChild(pElementContent2);

		const docNameElem = document.createElement('small');
		const currentInstance = Constants.getInstances.find(element => element.current);
		const currentXHTML = currentInstance?.docs.find(element => element.current);
		docNameElem.setAttribute('class', `${currentXHTML?.slug === factInfo?.file ? 'text-primary' : 'text-success'}`);
		docNameElem.setAttribute('data-cy', 'factFile');
		const docNameText = document.createTextNode(factInfo?.file ? factInfo.file : 'Unknown Location');
		docNameElem.appendChild(docNameText);

		aElement.appendChild(conceptWrapper);
		aElement.appendChild(factWrapper);
		container.appendChild(periodElem);
		container.appendChild(docNameElem);
		aElement.appendChild(container);
		factElem.appendChild(aElement);

		return factElem;
	},

	getFactBadge: (factInfo: any) => { 
		const hasDimensions = FactsGeneral.segmentHasProp(factInfo.segment, 'dimension');

		const spanElement = document.createElement('span');
		const nestedSpanElement = document.createElement('span');

		const title = `${factInfo.isAdditional ? ' Additional' : ''}${factInfo.isCustom ? ' Custom' : ''}${hasDimensions ? ' Dimension' : ''}`.trim();
		const label = `${factInfo.isAdditional ? ' A' : ''}${factInfo.isCustom ? ' C' : ''}${hasDimensions ? ' D' : ''}`.trim();
		nestedSpanElement.setAttribute('title', title.split(' ').join(' & '));
		nestedSpanElement.setAttribute('class', 'mx-1 my-0 badge text-bg-dark');

		const spanNestedElementContent = document.createTextNode(label.split(' ').join(' & '));

		nestedSpanElement.appendChild(spanNestedElementContent);
		spanElement.appendChild(nestedSpanElement);
		return spanElement;
	},

	specialSort: (unsortedArray: Array<{ id: string, isAdditional: boolean }>): string[] =>
	{
		return [...unsortedArray].sort((a, b) => +a.isAdditional - +b.isAdditional)
			.map(({ id }) => id);
	},

	// possibly refactor to more gerenal helper - depending if nested array's object property check are used else where 
	segmentHasProp: (segment: SegmentArray, prop: string): boolean => {
		if(Array.isArray(segment)) return segment.some(s => FactsGeneral.segmentHasProp(s as SegmentArray, prop));
		if(segment && typeof segment === 'object') {
			return prop in segment;
		} 
		return false
	}
};
