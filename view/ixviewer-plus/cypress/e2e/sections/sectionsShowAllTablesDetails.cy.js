import { selectors } from '../../utils/selectors'

describe(`Sections contain all links`, () => {
    /*
        Mustard menu was showing a lot of links ix viewer was not.  make sure all are there.  Here we are testing some of the missing ones.
    */

    it(`Reports contain all details tables policies links`, () => {
        cy.loadByAccessionNum('000000296918000044');
        // /Archives/edgar/data/2969/000000296918000044/apd-10xkx30sep2018.htm

        cy.get(selectors.sectionsHeader).click();

        // Schedule II Valuation and Qualifying Accounts
        cy.get('#sectionDoc-10-K--Notes-to-Financial-Statements').should('contain.text', 'Schedule II Valuation and Qualifying Accounts');

        // major accounting policies (policies)
        cy.get('#sectionDoc-10-K--Notes-to-Financial-Statements').should('contain.text', 'Major Accounting Policies (Policies)');
        
        // new accounting guidance (tables)
        cy.get('#sectionDoc-10-K--Notes-to-Financial-Statements').should('contain.text', 'New Accounting Guidance (Tables)');
        
        // new accounting guidance (balance sheet impacts) (details)
        cy.get('#sectionDoc-10-K--Notes-to-Financial-Statements').should('contain.text', 'New Accounting Guidance (Balance Sheet Impacts) (Details)');
    });
});
