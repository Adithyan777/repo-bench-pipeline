"""AI task benchmark pipeline. See docs/DESIGN.md."""

import warnings

# Target repos are parsed with ast at many historical revisions; their invalid escape
# sequences would otherwise flood stderr. Our own code is linted, so this hides nothing of ours.
warnings.filterwarnings("ignore", category=SyntaxWarning)
