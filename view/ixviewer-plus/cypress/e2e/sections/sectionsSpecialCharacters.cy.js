import { selectors } from '../../utils/selectors'
import { getByAccessionNum, loadBy } from '../../dataPlus/filingsFunnel.js'

describe(`Sections Special Characters - 817`, () => {
    // sometimes '-' and "'" (apostrophe) appear as "???" in report names.  It's actually that way in Filing summmary when it occurs.  
    // It's correct in metalinks though so lets make sure we grab the version of the shortName that doesn't have the encoding error.
    // ACTUALLY... WH instructed us to just use what's in filingSummary and not try to fix it downstream, so this test, if kept,
    // should actually test that string contains ???

    it(`should have correct encoding for apostrophe`, () => {
        cy.loadByAccessionNum('000121390026002587');
        cy.get(selectors.sectionsHeader).click();
        cy.get('#cat-body-Financial-Statements-sectionDoc-F-4-A > a:nth-child(3)').should('contain.text', "Statement of Changes in Members??? Equity (Unaudited)");
    });
    it(`should have correct encoding for hyphen`, () => {
        cy.loadByAccessionNum('000000445720000053');
        cy.get(selectors.sectionsHeader).click();
        // hopefully flexible, yet precise selector, it may move to different menu cat with other fixes
        cy.get('[id*="sectionDoc-10-K"] [contextref="DYCurrentYearToDate_ConsolidatedEntitiesAxis_ParentCompanyMember"][fact-name="us-gaap:IncomeTaxesPaidNet"]')
            .should('contain.text', "Uncategorized Items - uhal-20200331.htm");
    });
})
