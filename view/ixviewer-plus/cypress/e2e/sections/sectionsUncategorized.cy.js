import { selectors } from '../../utils/selectors'

describe(`Sections Uncategorized - 817`, () => {
/*
    if filings summ has:
        - report A - Cover
        - report B - Statements
        - report C - Cover
    report C should be categorized under Statments, not Cover.
    We don't allow backtracking of categorization, which sometimes means we ingore what filingSummary lists as menuCat
*/

    it(`Report should be under Uncategorized category, not under Cover`, () => {
        cy.loadByAccessionNum('000000445720000053');
        // /Archives/edgar/data/4457/000000445720000053/uhal-20200331.htm

        cy.get(selectors.sectionsHeader).click();

        // Uncategorized
        cy.get('#sectionDoc-10-K--Uncategorized').should('contain.text', 'Uncategorized Items - uhal-20200331.htm');

        // not Cover
        cy.get('#sectionDoc-10-K--Cover').should('not.contain.text', 'Uncategorized Items - uhal-20200331.htm');
    });
});
