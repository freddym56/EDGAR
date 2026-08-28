import { selectors } from "../../utils/selectors"

describe(`Not Found warning`, () => {
	it(`Should not appear when unhilighted fact is clicked`, () => {
		cy.loadByAccessionNum('000080786323000002');
		// https://www.sec.gov/ix?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm

		cy.hash().should('be.empty')
		
		cy.get(selectors.search).type('8-k')
		cy.get(selectors.search).type('{enter}')
		
		cy.get('[id="error-container"]').children().should('have.length', 0)
		
		cy.get('#fact-identifier-5').click()
		cy.get(selectors.factSidebarDetailDisplay)
		cy.hash().should('eq', '#fact-identifier-5')
		cy.get('[id="error-container"]').children().should('have.length', 0)
		
		cy.get('#fact-identifier-6').click()
		cy.get('[id="error-container"]').children().should('have.length', 0)

	})

	it(`Should not appear when unhilighted fact is clicked with fact list open`, () => {
		cy.loadByAccessionNum('000080786323000002');
		// https://www.sec.gov/ix?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm

		cy.hash().should('be.empty')
		
		cy.get(selectors.search).type('8-k')
		cy.get(selectors.search).type('{enter}')
		
		cy.get('[id="error-container"]').children().should('have.length', 0)

		cy.get('#fact-identifier-2').click()
		cy.get(selectors.factListDisplayBtn).click() 
		
		cy.get('#fact-identifier-5').click()
		cy.get(selectors.factSidebarDetailDisplay)
		cy.hash().should('eq', '#fact-identifier-5')
		cy.get('[id="error-container"]').children().should('have.length', 0)
		
		cy.get('#fact-identifier-6').click()
		cy.get('[id="error-container"]').children().should('have.length', 0)

	})

	it(`Should appear switching to list view while unhilighted fact is selected`, () => {
		cy.loadByAccessionNum('000080786323000002');
		// https://www.sec.gov/ix?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm

		cy.hash().should('be.empty')
		
		cy.get(selectors.search).type('8-k')
		cy.get(selectors.search).type('{enter}')
		
		cy.get('[id="error-container"]').children().should('have.length', 0)

		cy.get('#fact-identifier-5').click()
		cy.hash().should('eq', '#fact-identifier-5')

		cy.get(selectors.factListDisplayBtn).click() 
		cy.get('[id="error-container"]').children().should('have.length', 1)
	})


	it(`Should appear switching to split while unhilighted fact is selected`, () => {
		cy.loadByAccessionNum('000080786323000002');
		// https://www.sec.gov/ix?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm

		cy.hash().should('be.empty')
		
		cy.get(selectors.search).type('8-k')
		cy.get(selectors.search).type('{enter}')
		
		cy.get('[id="error-container"]').children().should('have.length', 0)

		cy.get('#fact-identifier-5').click()
		cy.hash().should('eq', '#fact-identifier-5')

		cy.get('#fact-details-panel-toolbar button[data-view="split"]').click()
		cy.get('[id="error-container"]').children().should('have.length', 1)
	})

	it(`Should show warn and deselect selected fact`, () => {
		cy.loadByAccessionNum('000080786323000002');
		// https://www.sec.gov/ix?doc=/Archives/edgar/data/807863/000080786323000002/mitk-20230104.htm

		cy.hash().should('be.empty')
		
		cy.get(selectors.search).type('8-k')
		cy.get(selectors.search).type('{enter}')
		
		cy.get('[id="error-container"]').children().should('have.length', 0)

		cy.get('#fact-identifier-2').click()
		cy.hash().should('eq', '#fact-identifier-2')

		cy.get(selectors.factListDisplayBtn).click() 
		cy.get(selectors.sidebarFact("2")).should('have.attr', 'selected-fact', 'true')

		cy.get('#fact-identifier-5').click()

		cy.get(selectors.factListDisplayBtn).click() 
		cy.get(selectors.sidebarFact("2")).should('have.attr', 'selected-fact', 'false')
	})
})