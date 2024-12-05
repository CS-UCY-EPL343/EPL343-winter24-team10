from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Add your app's URLs here
    # path('your_route/', your_view_function),
]
