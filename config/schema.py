from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import IsAuthenticated


schema_view = get_schema_view(
    openapi.Info(
        title= "StoreAPI",
        default_version= 'v1',
        description= 'API for Store'
    ),
    public= True,
    permission_classes= (IsAuthenticated,)
)