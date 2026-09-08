import { selectors } from "../../utils/selectors.mjs";
import { getByAccessionNum } from "../../dataPlus/filingsFunnel.js";

describe('Fact References', () => {
    it('Ensure all fact references are shown in fact detail panel', () => {
        cy.loadByAccessionNum('000005114323000021')
        cy.get('#fact-identifier-6').click()
        cy.get('#fact-details-references tbody').children().should('have.length', 622)
    })
});

