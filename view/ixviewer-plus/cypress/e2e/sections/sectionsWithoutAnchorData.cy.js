import { selectors } from '../../utils/selectors'

describe(`SectionsWithoutAnchorData`, () => {
    /*
    If a report lacks both uniqueAnchor and firstAnchor in metalinks.json we stil show it in sections, but it's not a link.
    sidenote, maybe it should have a tooltip, ""
    
    */

    it(`Report show Submissions report, but doesn't link to inline location`, () => {
        cy.loadByAccessionNum('000110465926005527');
        // /Archives/edgar/data/1626971/000110465926005527/tm263501d6_ex-filingfees.htm

        cy.get(selectors.sectionsHeader).click();

        cy.get('#cat-body-Cover-sectionDoc-EX-FILING-FEES').should('contain.text', 'Submission');

        // shouldn't be a link, not an <a> element, maybe a div
        cy.get('#cat-body-Cover-sectionDoc-EX-FILING-FEES [order="1"]').should('have.prop', 'tagName', 'div');
    });

    it(`Report show Cover report, but doesn't link to inline location`, () => {
        cy.loadByAccessionNum('000001731324000101');
        // /Archives/edgar/data/17313/000001731324000101/ck0000017313-20241030.htm

        cy.get(selectors.sectionsHeader).click();

        cy.get('#sectionDoc-424B2').should('contain.text', 'Cover'); // lacks anchor data

        // shouldn't be a link, not an <a> element, maybe a div
        cy.get('#cat-body-Cover-sectionDoc-424B2 > [order=1]').should('have.prop', 'tagName', 'div');
    });

    it(`Report show Cover report, but doesn't link to inline location`, () => {
        cy.loadByAccessionNum('000000296918000044');
        // /Archives/edgar/data/2969/000000296918000044/apd-10xkx30sep2018.htm

        cy.get(selectors.sectionsHeader).click();

        cy.get('#sectionDoc-10-K').should('contain.text', 'Income Taxes (Summary of Income Tax Examinations) (Details)'); // lacks anchor data
        
        cy.get('#cat-body-Financial-Statements-sectionDoc-10-K > [order=4]').should('have.prop', 'tagName', 'div');
    });
});
