from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',
         auth_views.LoginView.as_view(template_name='web/login.html'),
         name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(next_page='/login/'),
         name='logout'),
    path('api/', include('web.api.urls')),
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('', include('web.urls')),
]