/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

import { ConstantsFunctions } from "../constants/functions";
import { Pagination } from "../pagination/sideBarPagination";

export const FactsMenu = {

	toggle: (event: MouseEvent | KeyboardEvent) => {

		if (
			Object.prototype.hasOwnProperty.call(event, 'key') &&
			!((event as KeyboardEvent).key === 'Enter' || (event as KeyboardEvent).key === 'Space' || (event as KeyboardEvent).key === ' ')
		) {
			return;
		}

		if (event.target && (event.target as HTMLElement).classList && (event.target as HTMLElement).classList.contains('disabled')) {
			return;
		}
		FactsMenu.prepareForPagination();

	},
	
	updateFactMenuState: (newState: string) => {
		const navElement = document.getElementById('fact-display-nav') as HTMLElement
		const menuElement = navElement?.closest('.fact-menu-container') as HTMLElement | null;

		if (!menuElement) return;

		navElement.querySelectorAll('button.tab').forEach(btn => {
			btn.classList.remove('active')
		})

		const selectedFactId = ConstantsFunctions.getSelectedFactId()

		switch (newState) {
			case "fact-detail-display":
				menuElement.querySelector('#fact-detail-display-btn')?.classList.add('active')
				
				if (menuElement.dataset.factMenuDisplay !== "fact-split-display") {
					menuElement.querySelectorAll('#fact-details-panel-toolbar .view-btn[data-view]').forEach((btn) => btn.classList.toggle('active', btn.dataset.view === "detail"));
					menuElement.dataset.factMenuDisplay = newState;
				} 


		
				break;
			case "fact-list-display":
				menuElement.querySelector('#fact-list-display-btn')?.classList.add('active')

				menuElement.dataset.factMenuDisplay = newState; 
				if(selectedFactId) {
					Pagination.findFactAndGoTo(selectedFactId);
				}
				break;

			case "fact-split-display":
				menuElement.querySelector('#fact-detail-display-btn')?.classList.add('active')
				menuElement.dataset.factMenuDisplay = newState;
				if(selectedFactId) {
					Pagination.findFactAndGoTo(selectedFactId);
				}

				break;

			default:

				menuElement.dataset.factMenuDisplay = newState;
				break;
		}

		// menuElement.dataset.factMenuDisplay = newState;
	},
	updateFactMenuDisplay: (event: MouseEvent | KeyboardEvent) => {
		if ("key" in event && !(event.key === "Enter" || event.key === "Space" || event.key === " ")) {
			return;
		}
		const element = event.target as HTMLElement;
		const btnElement = element?.closest('.tab') as HTMLElement | null;
		const iconElement = element?.closest('.detail-icon')
		const factElment = element?.closest('[selected-fact]')


		if (btnElement?.id === 'fact-detail-display-btn' || iconElement || factElment) FactsMenu.updateFactMenuState('fact-detail-display');
		if (btnElement?.id === 'fact-list-display-btn') FactsMenu.updateFactMenuState('fact-list-display');
	},

	updateFactDetailDisplay: (event: MouseEvent | KeyboardEvent) => {
		if ("key" in event && !(event.key === "Enter" || event.key === "Space" || event.key === " ")) {
			return;
		}
		const element = event.target as HTMLElement;

		const viewBtn = element?.closest('.view-btn')

		const menuElement = element?.closest('.fact-menu-container') as HTMLElement | null;

		if (!menuElement) return;
		if (!viewBtn) return;


		viewBtn?.parentElement?.querySelectorAll('.view-btn').forEach(btn => btn.classList.toggle('active', btn.dataset.view === viewBtn.dataset.view))

		let newState = 'default'
		if (viewBtn?.dataset.view === 'detail') newState = 'fact-detail-display';
		if (viewBtn?.dataset.view === 'split') newState = 'fact-split-display';

		menuElement.dataset.factMenuDisplay = newState;
		FactsMenu.updateFactMenuState(newState)
	},

	/**
	 * @Description passes filtered fact set to Pagination.init()
	 */
	prepareForPagination: () => {
		ConstantsFunctions.setPagination();
	}
};
