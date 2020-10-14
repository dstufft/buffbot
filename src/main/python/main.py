import sys

from buffbot.ui import ApplicationContext


if __name__ == "__main__":
    ctx = ApplicationContext()
    sys.exit(ctx.run())
