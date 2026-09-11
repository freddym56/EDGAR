import { selectors } from '../../utils/selectors'

describe(`Sections Ordering Atypical - 817`, () => {
/*
    if filings summ has:
        - report A - Cover
        - report B - Statements
        - report C - Cover
    report C should be categorized under Statments, not Cover.
    We don't allow backtracking of categorization, which sometimes means we ingore what filingSummary lists as menuCat
*/

    it(`Balance Sheet (Parenthetical) should be under "Financial Statements" and "Notes Details"`, () => {
        cy.loadByAccessionNum('000110465926010897');
        // http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/1465369/000110465926019148/none-20260224xf4.htm

        /*
        There's actually 2 Balance Sheet (Parenthetical) reports in FilingSummary.xml
        1 should be under "Financial Statements"
        1 should be under "Notes Details"
        None should be under Cover
        */

        cy.get(selectors.sectionsHeader).click();

        // Financial-Statements
        cy.get('#sectionDoc-S-4-A--Financial-Statements').should('contain.text', 'Balance Sheet (Parenthetical)');

        // Notes-Details
        cy.get('#sectionDoc-S-4-A--Notes-Details').should('contain.text', 'Balance Sheet (Parenthetical)');

        // Cover
        cy.get('#sectionDoc-S-4-A--Cover').should('not.contain.text', 'Balance Sheet (Parenthetical)');
    });

    it(`should put reports in order of menu cats in filing summ`, () => {
        cy.loadByAccessionNum('000110465926019148');
        // http://localhost:3000/ix.xhtml?doc=/Archives/edgar/data/1465369/000110465926019148/none-20260224xf4.htm
        cy.get(selectors.sectionsHeader).click();

        // 2 links were incorrectly displayed under cover - make sure they are under Notes Details
        cy.get('#cat-body-Notes-Details-sectionDoc-F-4').should('contain.text', 'CONDENSED BALANCE SHEET (Parentheticals)');
        cy.get('#cat-body-Notes-Details-sectionDoc-F-4').should('contain.text', 'S-K 1603(a) SPAC Sponsor');
    });
})
