# Testing TODO List

This document tracks features that need test coverage but haven't been fully implemented yet.

## Debug Mode (Completed with Tests) ✅

### Debug Mode Features - 7 tests passing
- [x] Debug mode initialization with custom output folder
- [x] Debug mode disabled by default
- [x] ROM metadata saved to JSON files
- [x] Special characters in ROM names handled correctly
- [x] Platform folders created automatically
- [x] Error handling for missing ROM data
- [x] Debug output folder created on initialization

## Statistics Dashboard (Issue #18) - Completed Implementation, Tests Pending

### Statistics Calculation Features
- [ ] Total ROM counts (total, synced, pending, errors) calculated correctly
- [ ] Sync history retrieval with formatted timestamps
- [ ] Overall success rate calculation across all syncs
- [ ] Total synced count aggregation
- [ ] Platform breakdown with per-platform statistics
- [ ] Disk space estimation based on platform averages
- [ ] Sync trends aggregation by day
- [ ] Collection statistics with sync status counts

### Sync History Tracking
- [ ] Sync history table created automatically
- [ ] Each sync run recorded with timestamp
- [ ] Success/error/skipped counts tracked
- [ ] Duration calculated correctly
- [ ] Debug mode flag recorded
- [ ] History retrieval ordered by most recent

### Statistics Dashboard UI
- [ ] Summary cards display correct ROM counts
- [ ] Success rate progress bar renders
- [ ] Disk space estimate displays with formatting
- [ ] Platform breakdown table shows all platforms
- [ ] Platform progress bars calculated correctly
- [ ] Collection stats cards display all collections
- [ ] Sync history table shows recent syncs
- [ ] Success rate tags colored appropriately (green/yellow/red)
- [ ] No data message shown when no history exists
- [ ] Statistics link in navbar works

## UI/UX Features (Issue #15) - Completed Implementation, Tests Pending

### Base Template Features
- [ ] Dark mode toggle persistence across page reloads
- [ ] Toast notification system (auto-dismiss after 4 seconds)
- [ ] Toast notification manual close functionality
- [ ] Theme toggle icon swap (moon/sun)
- [ ] Navbar burger menu on mobile devices
- [ ] Flash message to toast conversion on page load

### Status Page Features
- [ ] Search functionality filters ROMs by name
- [ ] Search functionality filters ROMs by platform
- [ ] Clear search button resets filters
- [ ] Filter by status: All, Pending, Completed, Errors
- [ ] Filter buttons show active state
- [ ] Collection cards hide when no ROMs match filters
- [ ] Collection collapse/expand functionality
- [ ] Badge counters show correct counts (completed, pending, errors)
- [ ] Dropdown menu stops propagation (doesn't collapse collection)
- [ ] Reset status shows confirmation dialog
- [ ] Reset status shows loading toast
- [ ] Reset status shows success/error toast
- [ ] Reset status reloads page after success
- [ ] ROM items show correct status icons (spinner, check, error)
- [ ] Lazy loading for ROM cover images

### Config Page Features
- [ ] Password visibility toggle (eye icon)
- [ ] Form validation shows error states (is-danger class)
- [ ] Required field validation prevents submission
- [ ] Invalid input patterns show error toast
- [ ] Submit buttons show loading state during submission
- [ ] Input error states clear on typing
- [ ] URL pattern validation (https?://.+)
- [ ] Username/password min/max length validation
- [ ] Platform name pattern validation ([a-zA-Z0-9_-]+)
- [ ] Collection checkbox toggles enabled/disabled tags
- [ ] Help text displays for all input fields
- [ ] Icon-text combinations render correctly
- [ ] Table striping and hover effects work
- [ ] Responsive layout on mobile devices

### CSS/Animation Features
- [ ] Toast slideIn animation (translateX + opacity)
- [ ] Toast slideOut animation on close
- [ ] Loading spinner animation (spinAround keyframes)
- [ ] Card hover transform effect
- [ ] Button hover transform effect
- [ ] Smooth transitions (0.3s ease-in-out)
- [ ] Light mode CSS variables apply correctly
- [ ] Dark mode CSS variables apply correctly
- [ ] Badge styling (success, warning, danger)
- [ ] Responsive toast positioning on mobile

## Future Issues to Test (Not Yet Implemented)

### Issue #6: Sync Status = 2 Error Handling
- [ ] Display error details for failed syncs
- [ ] Retry button for individual ROMs
- [ ] Bulk retry functionality for all errors
- [ ] Error message display in UI
- [ ] Error count badge updates after retry

### Issue #7: Inefficient API Calls Optimization
- [ ] Batch API requests reduce total calls
- [ ] Caching prevents duplicate API calls
- [ ] Performance improvement measurable

### Issue #8: Configurable Scheduler Interval
- [ ] UI for setting scheduler interval
- [ ] Validation of interval values
- [ ] Scheduler respects new interval after change
- [ ] Persist interval setting to config

### Issue #9: Progress Indicators
- [ ] Progress bar shows sync progress
- [ ] Percentage calculation accurate
- [ ] Real-time updates during sync
- [ ] Progress indicator clears after completion

### Issue #10: Memory Issues with Large Files
- [ ] Streaming download implementation
- [ ] Memory usage stays below threshold
- [ ] Large file (>1GB) downloads successfully
- [ ] Cleanup after download completes

### Issue #11+: Minor Improvements
- [ ] Log rotation at specified size
- [ ] Log level configuration
- [ ] Improved error messages in logs
- [ ] Database backup functionality
- [ ] Export sync report to CSV/JSON

## Testing Strategy Notes

### Manual Testing Required
Since UI/UX features are frontend-heavy, manual testing in a browser is recommended:
1. Dark mode toggle and persistence
2. Toast notification animations
3. Search and filter interactions
4. Form validation visual feedback
5. Responsive design on different screen sizes

### Potential Automated Tests
Consider Selenium or Playwright for:
1. Toast notification lifecycle
2. Search/filter correctness
3. Form validation behavior
4. Theme persistence across page loads

### Integration Tests
Test JavaScript interactions with backend:
1. Reset status API call
2. Form submissions and redirects
3. Flash message to toast conversion
4. AJAX calls for dynamic content

## Test Coverage Goals

Current: 139 tests passing
- Issue #1: 2 tests (Django removal)
- Issue #2: 8 tests (Thread safety)
- Issue #3: 14 tests (Error handling)
- Issue #4: 8 tests (Duplicate handling)
- Issue #5: 62 tests (Input validation)
- Debug Mode: 7 tests (ROM metadata output)
- App tests: 14 tests (Flask routes)
- Background worker: 24 tests (Sync automation)

Target: Add ~50 more tests for UI/UX features (if automated testing implemented)
