/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

import { Modals } from "./modals";
import { Constants } from "../constants/constants";

export const ModalsSettings = {

	clickEvent: () => {
		/*
			if (
				Object.prototype.hasOwnProperty.call(event, 'key') &&
				!((event as KeyboardEvent).key === 'Enter' || (event as KeyboardEvent).key === 'Space')
			) {
				return;
			}
		*/

		const modal = document.getElementById('settings-modal')
		if (modal) {
			modal.classList.remove('d-none');
			Modals.bringToFront(modal)
		}

		document.getElementById('settings-modal-drag')?.focus();

		ModalsSettings.listeners();

		// set correct selected value
		(document.getElementById('scroll-position-select') as HTMLInputElement).value = Constants.scrollPosition;
		// set correct hover value
		(document.getElementById('hover-option-select') as HTMLInputElement).value = Constants.hoverOption.toString();
	},

	listeners: () => {
		Modals.initDrag(document.getElementById('settings-modal-drag') as HTMLElement);

		const closeBtn = document.getElementById('settings-modal-close');
		if(closeBtn) {
			closeBtn.onclick = () => Modals.hide('settings-modal');
			closeBtn.onkeyup = (event: KeyboardEvent) => {
				if (event.key == " " || event.key == "Space" || event.key == "Enter") {
					Modals.hide('settings-modal');
				}
			}
		}
	},

	scrollPosition: (event: Event) => {
		localStorage.setItem('scrollPosition', event.target.value);
		Constants.scrollPosition = event.target.value;
	},

	hoverOption: (event: Event) => {
		if (event?.target?.value === 'true') {

			localStorage.setItem('hoverOption', 'true');
			Constants.hoverOption = true;
		} else {

			localStorage.setItem('hoverOption', 'false');
			Constants.hoverOption = false;
		}
	}
};
