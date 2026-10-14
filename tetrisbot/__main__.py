"""Entry point: python -m tetrisbot [--no-overlay] [--bot-plays] [--gravity auto|low|high] [--locate] [--sim N] [--train N]"""
import argparse


def main():
    ap = argparse.ArgumentParser(prog="tetrisbot", description="TETR.IO Blitz bot (SingleYou/MS2/MS -> PC -> DPC loop)")
    ap.add_argument("--no-overlay", action="store_true", help="no on-screen window, hotkey only")
    ap.add_argument("--gravity", choices=["auto", "low", "high"],
                    help="override the saved gravity mode (high = soft drop after every input, safe at 20G)")
    ap.add_argument("--no-verify", action="store_true", help="skip per-piece board check (faster, less robust)")
    ap.add_argument("--locate", action="store_true", help="find the board on screen, print what is seen, exit")
    ap.add_argument("--sim", type=int, metavar="PIECES", help="play a simulated game (no TETR.IO needed)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bot-plays", action="store_true",
                    help="start with the bot playing (default: advisor - you play, it suggests)")
    ap.add_argument("--train", type=int, metavar="GAMES",
                    help="retrain the advisor's setup prior with this many self-play games")
    a = ap.parse_args()

    if a.train:
        from .model import train
        train(games=a.train)
        return

    if a.sim:
        from . import sim
        print(sim.run(a.sim, a.seed))
        return
    if a.locate:
        from .diagnose import locate_once
        locate_once()
        return
    from .handling import Handling
    h = Handling.load()          # edit with the overlay's "Handling…" window
    if a.gravity:
        h.gravity = a.gravity.upper()
    from .app import run
    run({"verify_board": not a.no_verify}, overlay=not a.no_overlay, handling=h, autoplay=a.bot_plays)


if __name__ == "__main__":
    main()
