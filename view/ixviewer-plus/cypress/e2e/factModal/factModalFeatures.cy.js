import { selectors } from "../../utils/selectors.mjs"
import { readFilingDataAccNum } from "../../dataPlus/filingsFunnel";

describe(`Fact Details Features`, () => {
      it('should show copy-able content with copy icon', () => {
        let filing = readFilingDataAccNum('000001469323000155')
        cy.loadFiling(filing)

        cy.get(selectors.factsHeader, { timeout: Number(filing.timeout) }).click()

        cy.get('a[data-id^="fact-identifier-"]').first().click()

        cy.get(selectors.factDetailDisplayBtn).click()

        cy.get(selectors.factModalCopyableContent).should('have.css', 'display', 'none')
        cy.get(selectors.factModalToggleCopyContent).click()
        cy.get(selectors.factModalToggleCopyContent).should('have.class', 'active')
        cy.get(selectors.factModalCopyableContent).should('have.css', 'display', 'block')
        
        
        
        // test toggle
        cy.get(selectors.factModalToggleCopyContent).click()
        cy.get(selectors.factModalToggleCopyContent).should('not.have.class', 'active')
        cy.get(selectors.factModalCopyableContent).should('have.css', 'display', 'none')
        cy.get(selectors.factModalToggleCopyContent).click()
        cy.get(selectors.factModalToggleCopyContent).should('have.class', 'active')
        cy.get(selectors.factModalCopyableContent).should('have.css', 'display', 'block')
    })

    it('Fact modal box copy contents should not change if you click the copy button multiple times', () => {
        let filing = readFilingDataAccNum('000001469323000155')
        cy.loadFiling(filing)
        cy.get('#fact-identifier-4', { timeout: Number(filing.timeout) }).click()
        cy.get(selectors.factDetailDisplayBtn).click()
        cy.get(selectors.factModalToggleCopyContent).click()
        cy.get(selectors.factModalCopyableContentEXP).then(($copyBox) => {
            const copyText = $copyBox.text()
            for(let n = 0; n < 6; n ++){
                cy.get(selectors.factModalToggleCopyContent).click()
            }
            cy.get(selectors.factModalCopyableContentEXP).should(($newCopy) => {
                expect($newCopy.text()).to.equal(copyText)
            })
        })
    })

    it("Image facts should be displayed in fact modal", () => {
        cy.loadByAccessionNum('000110465925018350');
        cy.get('[id="fact-identifier-1856"]').click()
        cy.get(selectors.factDetailDisplayBtn).click()
        cy.get(selectors.factExpandMoreLess).click().then(() => {
            cy.get('[data-cy="Fact-value"] img')
                .should('be.visible')
                .and('have.prop', 'naturalWidth')
                .should('be.greaterThan', 0)
        })
     })
})
