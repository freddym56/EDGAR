// import { filings } from '../../dataPlus/filingsWithUrls'
import { getFilingsSample } from '../../dataPlus/filingsFunnel.js'

let filingsSample = getFilingsSample(Cypress.env);

describe(`Metalinks requests`, () => {
	filingsSample.forEach((filing) => {

		it(`metalinks.json should load for ${filing?.ticker || filing.docName} ${filing.formType || filing.submissionType}`, () => {
			cy.requestMetaLinksPerHost(filing).then(resp => {
				expect(resp.status).to.equal(200)
			})
		})
	})
})

describe(`Metalinks UI alerts`, () => {
	it(`Metalinks fetch url with cross origin should show error alert`, () => {
		cy.vistByAccessionNum('000117625625000090', "&metalinks=http://localhost:3001/metalinks.json", (browser) => {
			cy.get('#error-container').should('contain.text', `The protocol, host name, and port number of the url parameter to fetch, if provided, must be identical to that of the Inline XBRL viewer (${browser.location.origin})`);
		})
	})

	it(`Metalinks fetch 404 should show error alert`, () => {
		cy.vistByAccessionNum('000117625625000090', "&metalinks=/metalinks.json", (browser) => {
			cy.get('#error-container').should('contain.text', `Error: 404; could not find "/metalinks.json"`);
		})
	})

	it(`Incorrect MetaLinks.json or htm file name should show error alert`, () => {
		cy.vistByAccessionNum('000117625625000090', "", (browser) => {
			const invaildHTM = browser.location.href.replace("20250930", "20250931")
			cy.visit(invaildHTM).then(() => {
				cy.get('#error-container').should('contain.text', `The document "aumn-20250931.htm.htm" was not found in MetaLinks.json. Available documents: aumn-20250930.htm.htm.`);
			})
		})
	})
})