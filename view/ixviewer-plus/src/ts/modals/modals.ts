/* Created by staff of the U.S. Securities and Exchange Commission.
 * Data and content created by government employees within the scope of their employment 
 * are not subject to domestic copyright protection. 17 U.S.C. 105.
 */

import { ConstantsFunctions } from "../constants/functions";
import { ModalsFormInformation } from "./form-information";

const resetModalZIndexes = () => {
	// resetting modal ZIndexes is useful to keep the ever incrementing topZIndex with an range
	const modals = Array.from(document.querySelectorAll<HTMLElement>('.dialog-box'));

	const getZIndex = (el: HTMLElement): number => {
		const zIndex = el.style.zIndex

		if (zIndex === '' || zIndex === 'auto') return BASE_Z_INDEX
		const zIndexNumber = Number(zIndex)

		return Number.isFinite(zIndexNumber) ? zIndexNumber : BASE_Z_INDEX
	}

	modals.sort((a, b) => getZIndex(a) - getZIndex(b));

	topZIndex = BASE_Z_INDEX;

	for (const modal of modals) {
		modal.style.zIndex = String(topZIndex);
		topZIndex += 1;
	}

}

const BASE_Z_INDEX = 100;
const MAX_Z_INDEX = 199;

let topZIndex = BASE_Z_INDEX;

export const Modals = {

	renderCarouselIndicators: (carouselId: string, indicatorId: string, carouselInformation: Array<{ 'dialog-title': string }>, currentSlide = 0) => {
		const elementToReturn = document.createDocumentFragment();
		if (currentSlide > 0) {
			currentSlide--;
		}
		carouselInformation.forEach((current, index) => {
			const activeSlide = (index === (currentSlide)) ? 'active' : '';

			const button = document.createElement('button');
			button.type = 'button';
			button.setAttribute('class', `${activeSlide} ix-focus`);
			button.setAttribute('data-bs-target', `#${carouselId}`);
			button.setAttribute('data-bs-slide-to', `${index}`);
			button.setAttribute('title', current['dialog-title']);
			button.setAttribute('tabindex', '16');

			elementToReturn.appendChild(button);
		});
		ConstantsFunctions.emptyHTMLByID(indicatorId);

		document.getElementById(indicatorId)?.appendChild(elementToReturn);
	},

	close: (event: Event | KeyboardEvent) => {

		if (Object.prototype.hasOwnProperty.call(event, 'key') && !((event as KeyboardEvent).key === 'Enter'
			|| (event as KeyboardEvent).key === 'Space' || (event as KeyboardEvent).key === ' ')) {
			return;
		}

		document.getElementById('fact-copy-paste')?.classList.add('d-none');

		window.removeEventListener('keyup', ModalsFormInformation.keyboardEvents);

		// to simplify things, we are going to go through and close every
		// dialog.
		const foundDialogs = document.querySelectorAll('.dialog-box');

		const foundDialogsArray = Array.prototype.slice.call(foundDialogs);

		foundDialogsArray.forEach((current) => {

			current.classList.remove('expand-modal');

			
			current.classList.add('d-none');
		});
	},

	hide: (modalId: string) => {
		const modal = document.getElementById(modalId)

		modal?.classList.remove('expand-modal')
		modal?.classList.add('d-none');
	},

	copyContent: (event: MouseEvent | KeyboardEvent, elementIdToCopy: string, copyPasteElement: string) => {

		if ("key" in event && !(event.key === "Enter" || event.key === "Space" || event.key === " ")) {
			return;
		}
		event.stopPropagation();

		const element = event.currentTarget as HTMLElement

		if (!document.getElementById(copyPasteElement)?.classList.contains('d-none')) {
			document.getElementById(copyPasteElement)?.classList.add('d-none');
			element.classList.remove('active')
		} else {
			const sectionToPopulate = '#' + copyPasteElement;
			document.getElementById(copyPasteElement)?.classList.remove('d-none');

			const foundCarouselPagesArray = Array.from(document.getElementById(elementIdToCopy)?.querySelectorAll('.carousel-item, .detail-item') || []);
			// TODO should we just put all of the innerText automatically into the user's clipboard?

			// th elements are the keys
			// td elements are the values
			let textToCopy = '';

			foundCarouselPagesArray.forEach((current) => {
				const foundInformation = current.querySelectorAll('table > * > tr');

				for (let nestedCurrent of foundInformation) {
					if (nestedCurrent.querySelector('th')?.innerText) {
						textToCopy += nestedCurrent.querySelector('th')!.innerText.trim() + ': ';
					}

					if (nestedCurrent.querySelector('td')) {
						const largeFactSelector = nestedCurrent.querySelector('td #collapse-modal');
						if (largeFactSelector instanceof HTMLElement) {
							textToCopy += '\n';
							textToCopy += largeFactSelector.innerText.trim().replace(/(\r\n|\n|\r)/gm, '');
							textToCopy += '\n';
						}
						else if (nestedCurrent.querySelector('td')?.innerText) {
							textToCopy += nestedCurrent.querySelector('td')!.innerText.trim().replace(/(\r\n|\n|\r)/gm, '');
							textToCopy += '\n';
						}
					}
				}
			});

			const textarea = document.querySelector(sectionToPopulate + " textarea");
			if (textarea != null) {
				textarea.textContent = textToCopy.trim();
			}

			element.classList.add('active')
		}
	},

	closeCopy: (input: string) => {
		(document.getElementById(input) as HTMLElement).classList.add('d-none');
	},

	clearAndCloseCopy: (input: string) => {
		(document.getElementById(input) as HTMLElement).classList.add('d-none');
		(document.querySelector(`#${input} textarea`) as HTMLElement).textContent = "";
		(document.getElementById('fact-modal-copy-content') as HTMLElement).classList.remove('active');
	},

	expandToggle: (
		event: MouseEvent | KeyboardEvent,
		idToTarget = '',
		idToExpand = 'fact-modal-expand',
		idToCompress = 'fact-modal-compress'
	) => {
		if (
			Object.prototype.hasOwnProperty.call(event, 'key') &&
			!((event as KeyboardEvent).key === 'Enter' ||
				(event as KeyboardEvent).key === 'Space' || (event as KeyboardEvent).key === ' ')
		) {
			return;
		}

		const modalElement = document.getElementById(idToTarget);
		modalElement?.classList.toggle('expand-modal');
		if (modalElement?.classList.contains('expand-modal')) {

			document.getElementById(idToExpand)?.classList.add('d-none');
			document.getElementById(idToCompress)?.classList.remove('d-none');
			document.getElementById(idToCompress)?.focus();

		} else {

			document.getElementById(idToExpand)?.classList.remove('d-none');
			document.getElementById(idToCompress)?.classList.add('d-none');
			document.getElementById(idToExpand)?.focus();
		}
	},

	initDrag: (element: HTMLElement) => {

		const modal = element.closest('.dialog-box') as HTMLElement | null;
		if (!modal) return;

		let offsetX = 0;
		let offsetY = 0;

		const dragElement = (event: MouseEvent) => {
			if (event.pageX >= 10 && event.pageX <= window.innerWidth - 14) {
				modal.style.left = (event.pageX - offsetX) + 'px'
			}

			if (event.pageY >= 60 && event.pageY <= window.innerHeight - 14) {
				modal.style.top = (event.pageY - offsetY) + 'px'
			}
		}

		const stopDrag = () => {
			document.removeEventListener('mousemove', dragElement)
			document.removeEventListener('mouseup', stopDrag)
		}


		element.onmousedown = (event: MouseEvent) => {
			offsetX = event.pageX - modal.offsetLeft;
			offsetY = event.pageY - modal.offsetTop;

			document.addEventListener('mousemove', dragElement);
			document.addEventListener('mouseup', stopDrag);
			return false;
		};


		modal.onmousedown = () => Modals.bringToFront(modal)
	},

	bringToFront: (modal: HTMLElement) => {

		if (topZIndex + 1 > MAX_Z_INDEX) {
			resetModalZIndexes()
		}

		if (Number(modal.style.zIndex) < topZIndex) {
			topZIndex += 1;
			modal.style.zIndex = topZIndex.toString();
		}
	}

};
