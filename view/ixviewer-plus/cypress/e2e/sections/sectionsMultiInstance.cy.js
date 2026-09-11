import { selectors } from '../../utils/selectors'
import { getByAccessionNum } from '../../dataPlus/filingsFunnel.js'

// let multiInstanceFiling = getByAccessionNum('0001079973-26-000209');

describe(`Sections Multi Instance - 817`, () => {
    it(`should change instances`, () => {
        cy.loadByAccessionNum('000107997326000209');
        cy.get(selectors.sectionsHeader).click();
        // 2 instances: "S-1" & "EX-FILING-FEES"
        // Make sure both are there

        // S-1 cover link should be there
        cy.get('#cat-body-Cover-sectionDoc-S-1 > a').should('exist');
        
        // Open "EX-FILING-FEES" sections
        cy.get('#instance-header-sectionDoc-EX-FILING-FEES').click();
        // 3 filing fees sections should be there
        cy.get('#cat-body-Cover-sectionDoc-EX-FILING-FEES > a:nth-child(1)').should('exist');
        cy.get('#cat-body-Cover-sectionDoc-EX-FILING-FEES > a:nth-child(2)').should('exist');
        cy.get('#cat-body-Cover-sectionDoc-EX-FILING-FEES > a:nth-child(3)').should('exist');
    })
    it(`should have 1 header for each instance`, () => {
        // there was a bug where it was showing ex C header between each other header
        cy.loadByAccessionNum('sbsef03')
        cy.get(selectors.sectionsHeader).click();
        cy.get('[id="sectionDoc-EX-99-C-SBSEF"]').should('have.length', 1);

    })
})
