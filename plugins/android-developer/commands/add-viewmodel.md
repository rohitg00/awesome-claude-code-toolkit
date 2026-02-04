# /add-viewmodel - Add ViewModel

Create an Android ViewModel with proper state management and data flow.

## Steps

1. Ask the user for the ViewModel name and the data it manages
2. Create the ViewModel class extending androidx.lifecycle.ViewModel
3. Define sealed interfaces for UI state, UI events, and side effects
4. Initialize StateFlow for the UI state with a sensible default
5. Add repository or use case dependencies via constructor injection (Hilt)
6. Implement event handling: map user actions to state changes
7. Add error handling with proper error state propagation
8. Implement data loading with coroutines in viewModelScope
9. Add retry logic for failed network requests
10. Create unit tests with fake repositories and TestDispatcher
11. Add Hilt @Inject annotation and module binding
12. Document the state machine: states, events, and transitions

## Rules

- Never expose mutable state directly; use private MutableStateFlow with public StateFlow
- Use sealed interfaces for UI state to ensure exhaustive handling
- Handle all coroutine exceptions with CoroutineExceptionHandler
- Cancel ongoing operations in onCleared if needed
- Use SavedStateHandle for surviving process death
- Keep ViewModels thin; delegate business logic to use cases
- Do not reference Activity, Context, or View classes in ViewModels
