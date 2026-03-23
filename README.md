# MeatheadLifts

MeatheadLifts is a simple web app for running a Stronglifts 5x5 lifting program with an A/B workout rotation.

It lets you:
- Log sets and reps quickly with tap-friendly buttons
- Track workout history on a calendar
- Edit/delete previous sessions
- Use a built-in plate calculator
- Add notes per lift
- Manage users with admin controls

This app was vibe-coded while working out.

![Overview](https://github.com/bobbywaz/meatheadlifts/blob/main/ss1.png?raw=true)
## Run with Docker Compose

```yaml
services:
  meatheadlifts:
    image: ghcr.io/bobbywaz/meatheadlifts:latest
    container_name: meatheadlifts
    restart: unless-stopped
    ports:
      - "18995:8000"
    environment:
      - TZ=America/New_York
      # Option 1: Set an initial admin on first run (recommended)
      - INITIAL_ADMIN_USERNAME=admin@example.com
      - INITIAL_ADMIN_PASSWORD=your-secure-password
      # Option 2: Leave the above unset, and the first user to sign up
      # on the /signup page will automatically become an admin.
      #
      # Set your own random long secret in production:
      - SECRET_KEY=replace-with-a-long-random-secret
    volumes:
      - ./meatheadlifts-data:/app/data
```

Then open:
- `http://YOUR_SERVER_IP:18995/login`

**Initial Setup:**
On the first run, you can either:
1. Provide `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` via environment variables.
2. Go to `/signup` and create the first account, which will automatically be granted admin privileges.


![Plate Calc](https://github.com/bobbywaz/meatheadlifts/blob/main/ss2.png?raw=true)


![Calendar](https://github.com/bobbywaz/meatheadlifts/blob/main/ss3.png?raw=true)


