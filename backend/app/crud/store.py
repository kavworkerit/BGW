from app.crud.base import CRUDBase
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate


class CRUDStore(CRUDBase[Store, StoreCreate, StoreUpdate]):
    pass


store_crud = CRUDStore(Store)