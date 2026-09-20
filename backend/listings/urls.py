from django.urls import path
from . import views

urlpatterns = [
    path("faculties/", views.FacultyListView.as_view()),
    path("faculties/<int:pk>/", views.FacultyDetailView.as_view()),
    path("boarding-houses/", views.BoardingHouseListView.as_view()),
    path("boarding-houses/recommended/", views.BoardingHouseRecommendedView.as_view()),
    path("boarding-houses/<int:pk>/", views.BoardingHouseDetailView.as_view()),
    path("road-segments/", views.RoadSegmentListView.as_view()),
    path("route/", views.RouteView.as_view()),
    path("heatmap/", views.HeatmapView.as_view()),
]
