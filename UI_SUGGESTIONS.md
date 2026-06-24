# MeatheadLifts UI Improvement Suggestions

Based on an assessment of the visual screenshots and vanilla HTML/CSS/JS frontend logic, here are several suggested UI and UX improvements:

## 1. Workout Tracking Enhancements
*   **Weight Steppers (+ / -)**: The current UI relies on raw `<input type="number">` fields for exercise weight (`.weight-input`). Mobile numeric keyboards can be clunky. Adding visual `+` and `-` buttons alongside the input (e.g., +/- 2.5lb or 5lb jumps) would make adjusting weights during a workout much more tap-friendly, fitting the mobile-first design better.
*   **Visual Set Completion Order**: Right now, the `set-btn` buttons cycle through 5, 4, 3, 2, 1, 0 but they are simple circular elements. Highlighting the *next expected set* to complete or graying out un-started sets versus just changing the number and turning them dark gray on `0` would increase clarity on workout progress.
*   **Rest Timer**: A built-in rest timer that starts automatically when a user taps a set button (e.g., triggering a 90-second or 3-minute countdown) would be highly beneficial for the Stronglifts 5x5 protocol. This could be displayed in a sticky bar or inline below the active exercise.

## 2. Layout and Navigation
*   **Sticky "Finish" Button**: The "Finish" button is placed under the workout list. For users with multiple exercises or a long scroll, especially on smaller screens, it would be useful to have a sticky or floating "Finish" button (or a global save indicator) that remains accessible without scrolling back up or down.
*   **Collapsible Exercise Cards**: Allow users to collapse/expand individual exercise cards (`.exercise-card`) once they've finished all 5 sets for that lift. This would clean up the view and keep the user focused on the remaining exercises.
*   **Tabbed Interface / Floating Action Bar**: The app piles everything (Workout, Plate Calc, Calendar, Recent History) vertically onto a single page `index.html`. Using a bottom navigation bar or simple tabs to switch views (e.g., "Log", "Calendar", "Calc") would vastly reduce scrolling and keep the cognitive load lower for the active workout view.

## 3. Plate Calculator Improvements
*   **Visual Plate Representation**: The plate calculator currently outputs text (e.g., "45 x 1, 25 x 1"). It could render a visual diagram of the barbell end with the required plates stacked on the sleeve, making it instantly recognizable without reading text.
*   **Save/Restore Configurations**: While the plate config is saved to `localStorage`, the UI doesn't make it obvious. A "Reset to Standard Gym" button would be helpful if the user messed up their custom plate inventory.
*   **Quick Jumps**: Quick add buttons for common working weights (e.g., "Add 10 lbs") could automatically update the plate calculator input.

## 4. Visuals and Theming
*   **Theme Toggle (Light/Dark Mode)**: The app has a hardcoded dark theme (e.g., `--bg: #0f1115;`). Adding CSS variables for a light theme and a toggle switch would be great for users training in brightly lit environments or outdoor gyms where dark mode has too much glare.
*   **Better Contrast on Disabled/Inactive States**: The `0` rep state (`.set-btn.zero`) uses `#3d414a` on the dark theme. It could use a more stark visual indicator, like a strikethrough or lower opacity, to emphasize it's skipped/zeroed out completely, as opposed to just being another color.
*   **Calendar State Clarity**: The yellow border for `future-workout` and the green dot for `workout-done` are good. However, missed scheduled workouts don't seem to have a strong red/alert visual state on the calendar grid, making it harder to track missed sessions at a glance.

## 5. History and Detail Views
*   **Inline Editing over Form Switch**: "Edit" on a recent workout triggers `startEditingSession`, throwing the user back to the top of the page with the workout form populated. For history, it would be cleaner to edit via an inline modal or a dedicated sub-view so users don't lose context of where they were in the history list.

By implementing these changes, MeatheadLifts would improve its "vibe-coded" mobile-first usability, making the core loop of tracking sets and checking plates faster and more satisfying.