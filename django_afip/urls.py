from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^populate_models$', views.populate_models, name='populate_models'),
]
