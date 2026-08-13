import { selectors } from '../../utils/selectors'

describe(`Sections relies on Filing Summary for menu cat`, () => {
    /*
        Schedule II Valuation and Qualifying Accounts
        ^ lacks groupType and menuCat in metalinks.json
        If we're correctly using filingsummary instead this shouldn't be a problem.
        Also it's uncategorized, but it should be in
    
    */

    it(``, () => {
        cy.loadByAccessionNum('000000296919000051');
        // /Archives/edgar/data/2969/000000296919000051/apd-10xkx30sep19.htm

        cy.get(selectors.sectionsHeader).click();

        // should Cover should exist (cover report used to be filed under reports erroneously)
        cy.get('#sectionDoc-10-K--Notes-to-Financial-Statements').should('contain.text', 'Schedule II Valuation and Qualifying Accounts');
    });
});
