import { selectors } from '../../utils/selectors'

describe(`Sections Don't show S reports`, () => {

    // "S" reports have keys with "S", like "S1", "S2"
    // Viewer had been showing them as they are in metalinks, but they are not in FilingSummary.
    it(`2 "S" reports should not be shown`, () => {
        cy.loadByAccessionNum('000000513823000067');
        // /Archives/edgar/data/5138/000000513823000067/a2023n1a.htm

        cy.get(selectors.sectionsHeader).click();

        // Uncategorized
        cy.get('#sectionDoc-485BPOS--RR-Summaries').should('not.contain.text', 'S 000012125 [Member]');

        // not Cover
        cy.get('#sectionDoc-485BPOS--RR-Summaries').should('not.contain.text', 'Document and Entity Information');
    });
});
