### Autoblox: Roblox Piano Auto Player

automation script for Roblox(Sober)

## System Requirements

- **Linux**: electricity

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/khuza08/autoblox.git
   cd autoblox
   ```

2. Create a Virtual Environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. (Optional) Grant input permissions to avoid running as root:
   ```bash
   sudo chmod 666 /dev/uinput
   ```

## How to Run

For the best performance (Real-Time Priority), use the provided runner script:

```bash
chmod +x run.sh
./run.sh
```

The app will prompt for your **sudo** password to enable the `chrt -f 99` kernel policy (Real-Time FIFO scheduling), ensuring the highest timing precision.

**Credits**: look at auto.py file. <br>
**Disclaimer**: Use this script responsibly. im not responsible for any bans or penalties imposed by roblowks.
