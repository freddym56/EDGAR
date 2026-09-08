
const createStore = (initial = { enabled: false }) => {
    let state = { ...initial };
    const subscribers = new Set();

    const getState = () => ({ ...state });

    const setState = (next) => {

        const prev = state;
        const changed = Object.keys(next).some(k => next[k] !== prev[k]);
        if (!changed) return;

        state = { ...prev, ...next };
        subscribers.forEach(fn => fn(getState()));
    };

    const subscribe = (fn) => {
        subscribers.add(fn);
        fn(getState());
        return () => subscribers.delete(fn);
    };

    return { getState, setState, subscribe };
};

const toggleStore = createStore({ enabled: false });

function bindToggleButton(el) {
    const render = (state) => {
        el.setAttribute('aria-checked', String(state.enabled));
        const label = el.querySelector('.toggle__label');
        if (label) {
            label.textContent = `Feature: ${state.enabled ? 'On' : 'Off'}`;
        }
    };

    const unsubscribe = toggleStore.subscribe(render);

    el.addEventListener('click', () => {
        const { enabled } = toggleStore.getState();
        toggleStore.setState({ enabled: !enabled });
    });

    el.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            const { enabled } = toggleStore.getState();
            toggleStore.setState({ enabled: !enabled });
        }
    });


    return () => {
        unsubscribe();
        el.replaceWith(el.cloneNode(true)); // strip listeners
    };
}

const sidenavToggle = document.getElementById('toggle-sidenav');
const dockToggle = document.getElementById('toggle-dock');

bindToggleButton(sidenavToggle);
bindToggleButton(dockToggle);


const saved = localStorage.getItem('feature-enabled');
if (saved !== null) {
    toggleStore.setState({ enabled: saved === 'true' });
}

toggleStore.subscribe((state) => {
    localStorage.setItem('feature-enabled', String(state.enabled));
});


const bc = 'feature-sync';
const channel = ('BroadcastChannel' in window) ? new BroadcastChannel(bc) : null;

if (channel) {
    toggleStore.subscribe((state) => channel.postMessage(state));

    channel.addEventListener('message', (ev) => {
        const { enabled } = toggleStore.getState();
        if (ev.data && ev.data.enabled !== enabled) {
            toggleStore.setState({ enabled: ev.data.enabled });
        }
    });
} else {
    window.addEventListener('storage', (e) => {
        if (e.key === 'feature-enabled') {
            const next = e.newValue === 'true';
            const { enabled } = toggleStore.getState();
            if (next !== enabled) toggleStore.setState({ enabled: next });
        }
    });
}
