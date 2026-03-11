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
      # Change these on first run:
      - INITIAL_ADMIN_USERNAME=admin@meatheadlifts.local
      - INITIAL_ADMIN_PASSWORD=ChangeMe123
      # Set your own random long secret in production:
      - SECRET_KEY=replace-with-a-long-random-secret
    volumes:
      - ./meatheadlifts-data:/app/data
```

Then open:
- `http://YOUR_SERVER_IP:18995/login`
Default first-run login:
- Email: `admin@meatheadlifts.local`
- Password: `ChangeMe123`

Change the default password immediately after first login.


![Plate Calc](https://github.com/bobbywaz/meatheadlifts/blob/main/ss2.png?raw=true)


![Calendar](https://github.com/bobbywaz/meatheadlifts/blob/main/ss3.png?raw=true)


