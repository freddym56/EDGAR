import { selectors } from '../../utils/selectors'

describe(`Sections Nonstatements filings show cover in cover`, () => {
    /*
    If a report lacks both uniqueAnchor and firstAnchor in metalinks.json we stil show it in sections, but it's not a link.
    sidenote, maybe it should have a tooltip, ""
    
    */

    it(`Cover in menu cat cover`, () => {
        cy.loadByAccessionNum('000000217824000043');
        // /Archives/edgar/data/2178/000000217824000043/ae-20240327.htm

        cy.get(selectors.sectionsHeader).click();

        // should Cover should exist (cover report used to be filed under reports erroneously)
        cy.get('#cat-body-Reports-sectionDoc-DEF-14A').should('exist');
    });
});
