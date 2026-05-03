import { computed, reactive } from 'vue';

export class Store<T extends Record<string, any>> {
  public state: T;

  private callbacks = new Set<() => void>();

  constructor(initialState: T, options?: { onUpdate?: () => void }) {
    this.state = reactive(initialState) as T;
    if (options?.onUpdate) {
      this.callbacks.add(options.onUpdate);
    }
  }

  setState(updater: (prev: T) => Partial<T>) {
    const newState = updater(this.state);
    Object.assign(this.state, newState);
    this.callbacks.forEach((cb) => cb());
  }
}

export function useStore<T extends Record<string, any>, U = T>(
  store: Store<T>,
  selector?: (state: T) => U,
) {
  return computed(() => {
    return selector ? selector(store.state) : store.state;
  });
}
