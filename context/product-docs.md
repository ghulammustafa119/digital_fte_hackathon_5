# FlowBoard - Product Documentation

## Getting Started

### Creating Your Account
1. Visit www.flowboard.io/signup
2. Enter your email and create a password (min 8 characters, 1 uppercase, 1 number)
3. Verify your email address
4. Set up your workspace name
5. Invite team members (optional)

### Creating Your First Project
1. Click the **"+ New Project"** button in the sidebar
2. Choose a template or start blank
3. Name your project and set visibility (Public/Private)
4. Add team members to the project

---

## Task Management

### Creating Tasks
- Click **"+ Add Task"** in any board column
- Required: Task title
- Optional: Description, assignee, due date, priority, labels, custom fields

### Task Properties
| Property | Description | Options |
|----------|-------------|---------|
| Status | Current state | To Do, In Progress, In Review, Done, Archived |
| Priority | Urgency level | Low, Medium, High, Urgent |
| Assignee | Responsible person | Any workspace member |
| Due Date | Deadline | Any future date |
| Labels | Color-coded tags | Custom labels per project |
| Estimate | Time estimate | Hours or story points |
| Custom Fields | User-defined | Text, Number, Date, Dropdown, Checkbox |

### Task Views
- **Kanban Board**: Drag-and-drop cards between columns
- **List View**: Spreadsheet-style with sortable columns
- **Calendar View**: Tasks shown by due date
- **Timeline (Gantt)**: Visual project timeline with dependencies (Pro+)

### Subtasks
- Any task can have unlimited subtasks
- Subtasks inherit the parent task's project
- Progress bar shows subtask completion percentage

### Task Dependencies (Pro+)
- **Blocking**: Task A blocks Task B
- **Waiting on**: Task A waits for Task B
- Dependencies shown in Timeline view

---

## Collaboration

### Comments
- Add comments to any task
- Use **@mention** to notify team members
- Attach files to comments (max 25MB per file)
- Edit or delete your own comments within 24 hours

### Real-time Updates
- Changes sync instantly across all users
- Presence indicators show who's viewing a task
- Activity feed shows all recent changes

### Notifications
- **In-app**: Bell icon shows unread notifications
- **Email**: Daily digest or instant (configurable in Settings > Notifications)
- **Slack**: Connect Slack channel to receive project updates (Pro+)
- **Mobile Push**: Enable in mobile app settings

---

## Time Tracking (Pro+)

### Using the Timer
1. Open any task
2. Click the **clock icon** to start the timer
3. Timer runs in the background (visible in top bar)
4. Click **Stop** to log the time entry

### Manual Time Entry
1. Open a task > click **"Log Time"**
2. Enter date, duration, and optional note
3. Click **Save**

### Time Reports
- Navigate to **Reports > Time Tracking**
- Filter by: Project, Team Member, Date Range
- Export as CSV or PDF

---

## Integrations (Pro+)

### Slack Integration
1. Go to **Settings > Integrations > Slack**
2. Click **"Connect to Slack"**
3. Authorize FlowBoard in Slack
4. Choose which project notifications go to which Slack channel
- Task created, completed, commented, assigned
- Due date reminders

### GitHub Integration
1. Go to **Settings > Integrations > GitHub**
2. Connect your GitHub account
3. Link repositories to projects
4. Features: Auto-create tasks from issues, link commits to tasks, PR status on task cards

### Google Drive Integration
1. Go to **Settings > Integrations > Google Drive**
2. Authorize access
3. Attach Google Docs/Sheets/Slides directly to tasks
4. Preview Google files inside FlowBoard

### Zapier Integration
- Connect FlowBoard with 5,000+ apps via Zapier
- Popular Zaps: Gmail to task, Form submission to task, CRM deal to task

---

## Automations (Pro+)

### Built-in Automations
- **Auto-assign**: When task moves to "In Progress", assign to [user]
- **Due date reminder**: Notify assignee 1 day before due date
- **Status update**: When all subtasks done, move parent to "Done"
- **Label trigger**: When label "Bug" added, set priority to "High"

### Custom Automation Rules
- **Trigger**: When [event] happens
- **Condition**: If [condition] is met (optional)
- **Action**: Then do [action]

Available triggers: Task created, status changed, assignee changed, due date passed, comment added
Available actions: Change status, assign user, add label, send notification, move to project

---

## Reports & Dashboards (Business+)

### Available Reports
1. **Team Velocity**: Tasks completed per sprint/week
2. **Burndown Chart**: Remaining work over time
3. **Workload View**: Tasks per team member
4. **Cycle Time**: Average time from "To Do" to "Done"
5. **Overdue Tasks**: Tasks past their due date

### Custom Dashboards
- Create custom dashboards with widgets
- Share dashboards with team
- Auto-refresh every 5 minutes

---

## Account & Billing

### Changing Your Plan
1. Go to **Settings > Billing**
2. Click **"Change Plan"**
3. Select new plan
4. Changes take effect immediately
5. Prorated charges/credits applied automatically

### Adding/Removing Users
- **Add**: Settings > Members > Invite by email
- **Remove**: Settings > Members > Click user > Remove
- Billing adjusts automatically on next cycle

### Cancellation
- Go to **Settings > Billing > Cancel Subscription**
- Data retained for 30 days after cancellation
- Export your data before cancelling (Settings > Export)

### Data Export
- Go to **Settings > Export**
- Choose format: JSON or CSV
- Includes: Tasks, comments, time entries, files list
- Export ready within 24 hours (download link sent via email)

---

## Security

### Password Reset
1. Go to login page > click **"Forgot Password?"**
2. Enter your registered email
3. Check email for reset link (valid for 1 hour)
4. Create new password (min 8 chars, 1 uppercase, 1 number)
5. If you don't receive the email, check spam folder or contact support

### Two-Factor Authentication (2FA)
1. Go to **Settings > Security > Two-Factor Authentication**
2. Click **"Enable 2FA"**
3. Scan QR code with authenticator app (Google Authenticator, Authy)
4. Enter the 6-digit code to verify
5. Save backup codes in a safe place

### SSO (Business+)
- Supported providers: Google, Microsoft, Okta, OneLogin
- Setup: Settings > Security > SSO Configuration
- Contact support for custom SAML configuration

---

## API Access (Pro+)

### Authentication
- Generate API key: Settings > API > Generate Key
- Include in header: `Authorization: Bearer YOUR_API_KEY`
- Rate limit: 100 requests/minute (Pro), 500 requests/minute (Business)

### Common Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/tasks | GET | List all tasks |
| /api/v1/tasks | POST | Create a task |
| /api/v1/tasks/{id} | GET | Get task details |
| /api/v1/tasks/{id} | PUT | Update a task |
| /api/v1/projects | GET | List projects |
| /api/v1/users | GET | List workspace members |
| /api/v1/time-entries | GET | List time entries |

### Webhooks
- Configure at Settings > API > Webhooks
- Events: task.created, task.updated, task.deleted, comment.created
- Payload format: JSON with event type and resource data

---

## Troubleshooting

### Common Issues

**Q: I can't log in**
A: Try resetting your password. If using SSO, ensure your company's identity provider is working. Clear browser cache and cookies.

**Q: Tasks are not syncing**
A: Check your internet connection. Try refreshing the page (Ctrl+F5). If issue persists, check our status page at status.flowboard.io.

**Q: I can't see a project**
A: The project may be set to Private. Ask the project owner to add you as a member.

**Q: File upload fails**
A: Maximum file size is 25MB. Supported formats: Images, PDFs, Documents, Spreadsheets, ZIP files. Check your storage quota in Settings > Storage.

**Q: Email notifications not working**
A: Check Settings > Notifications > Email. Ensure notifications are enabled. Check your spam/junk folder. Add noreply@flowboard.io to your contacts.

**Q: Mobile app keeps crashing**
A: Update to the latest version from App Store/Play Store. Clear app cache. If issue persists, uninstall and reinstall.

**Q: Automation not triggering**
A: Verify the automation is enabled (Settings > Automations). Check trigger conditions match. Note: Automations have a 1-minute delay for batch processing.

**Q: Can't connect Slack integration**
A: Ensure you have admin permissions in both FlowBoard and Slack. Try disconnecting and reconnecting. Check that third-party apps are allowed in your Slack workspace settings.
