"""Signal Collection (docs/TECHNICAL-SPEC-V1.md §18 component 1).

Four modular collectors, each an independent unit behind the same ``Signal``
output contract (I8): ``web_search``, ``youtube``, ``tiktok_creative_center``,
``internal_data``. Adding or replacing one does not touch the rest of the pipeline.

Collection is the first stage that writes to ``data/<run_id>/`` — one raw capture
per signal (§6.7). It degrades per source and only hard-fails when every
configured source fails (§14). In ``replay`` mode no live source is contacted;
recorded raw captures drive the run (§22).
"""

# Importing the collector modules registers them in base.DEFAULT_COLLECTORS.
from . import internal_data as _internal_data  # noqa: F401,E402
from . import tiktok as _tiktok  # noqa: F401,E402
from . import web_search as _web_search  # noqa: F401,E402
from . import youtube as _youtube  # noqa: F401,E402

