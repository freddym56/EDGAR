import { selectors } from "../../utils/selectors.mjs"
import { readFilingDataAccNum } from "../../dataPlus/filingsFunnel";

describe(`Modal Features`, () => {
    it('should be able move modal independently', () => {
        let filing = readFilingDataAccNum('000001469323000155')
        cy.loadFiling(filing)

        let originalPos = {}

        cy.openFormInfo()

        cy.get(selectors.formInfoModal).then(($modal) => {
            originalPos = $modal.position()
        })

        cy.get(selectors.formInformationDrag)
            .trigger('mouseover', { force: true })
            .trigger('mousedown', { which: 1 }) 

        cy.document().then((doc) => {
            cy.wrap(doc).trigger('mousemove', {
                pageX: 150,
                pageY: 800,
            })

            cy.wrap(doc).trigger('mouseup', { force: true })
        })
             
        cy.get(selectors.formInfoModal).then(($modal) => {
            expect($modal.position()).not.deep.eq(originalPos)
        })

        cy.openSettings()

        cy.get(selectors.settingsModal).then(($modal) => {
            originalPos = $modal.position()
        })
        cy.get(selectors.settingsDrag)
            .trigger('mouseover', { force: true })
            .trigger('mousedown', { which: 1 })


        cy.document().then((doc) => {
            cy.wrap(doc).trigger('mousemove', {
                pageX: 150,
                pageY: 800,
            })

            cy.wrap(doc).trigger('mouseup', { force: true })
        })
            
        cy.get(selectors.settingsModal).then(($modal) => {
            expect($modal.position()).not.deep.eq(originalPos)
        })

    });


    it('should be able close modal independently', () => {
        let filing = readFilingDataAccNum('000001469323000155')
        cy.loadFiling(filing)


        cy.openSettings()
        cy.openFormInfo()

        cy.get(selectors.formInformationClose).click()
        cy.get(selectors.settingsModal).should('not.have.css', 'display', 'none')
        cy.get(selectors.formInfoModal).should('have.css', 'display', 'none')
    })


    it('should bring modal to front when click', () => {
        let filing = readFilingDataAccNum('000001469323000155')
        cy.loadFiling(filing)
        let originalPos = {}


        cy.openSettings();

        cy.get(selectors.settingsModal).then(($modal) => {
            originalPos = $modal.position()
        })
        cy.get(selectors.settingsDrag)
            .trigger('mouseover', { force: true })
            .trigger('mousedown', { which: 1 })


        cy.document().then((doc) => {
            cy.wrap(doc).trigger('mousemove', {
                pageX: 500,
                pageY: 0,
            })

            cy.wrap(doc).trigger('mouseup', { force: true })
        })

        cy.openFormInfo();

        cy.get(selectors.formInfoModal).then(($topEl) => {
            const topRect = $topEl[0].getBoundingClientRect();

            cy.get(selectors.settingsModal).then(($bottomEl) => {

                const bottomRect = $bottomEl[0].getBoundingClientRect();
                cy.expect(topRect.top <= bottomRect.bottom && topRect.bottom >= bottomRect.top).to.be.true;
                cy.expect(topRect.left <= bottomRect.right && topRect.right >= bottomRect.left).to.be.true;
            })
        })




        cy.get(selectors.settingsModal).then(($topEl) => {
            const topRect = $topEl[0].getBoundingClientRect();

            cy.get(selectors.formInfoModal).then(($bottomEl) => {

                const bottomRect = $bottomEl[0].getBoundingClientRect();
                cy.expect(topRect.top <= bottomRect.bottom && topRect.bottom >= bottomRect.top).to.be.true;
                cy.expect(topRect.left <= bottomRect.right && topRect.right >= bottomRect.left).to.be.true;
            })
        })


    })
})
