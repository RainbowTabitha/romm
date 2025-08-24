from .collections_handler import DBCollectionsHandler
from .firmware_handler import DBFirmwareHandler
from .platforms_handler import DBPlatformsHandler
from .roms_handler import DBRomsHandler
from .rom_verification_handler import DBRomVerificationHandler
from .saves_handler import DBSavesHandler
from .screenshots_handler import DBScreenshotsHandler
from .states_handler import DBStatesHandler
from .stats_handler import DBStatsHandler
from .users_handler import DBUsersHandler

db_firmware_handler = DBFirmwareHandler()
db_platform_handler = DBPlatformsHandler()
db_rom_handler = DBRomsHandler()
db_rom_verification_handler = DBRomVerificationHandler()
db_save_handler = DBSavesHandler()
db_screenshot_handler = DBScreenshotsHandler()
db_state_handler = DBStatesHandler()
db_stats_handler = DBStatsHandler()
db_user_handler = DBUsersHandler()
db_collection_handler = DBCollectionsHandler()
