from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.viewsets import OwnedModelViewSet

from .models import Link, Person
from .serializers import LinkSerializer, PersonSerializer
from .services import build_graph

class PersonViewSet(OwnedModelViewSet):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    search_fields = ["name", "role", "email"]

class LinkViewSet(OwnedModelViewSet):
    serializer_class = LinkSerializer
    queryset = Link.objects.all()
    filterset_fields = ["source_type", "target_type", "relation"]

class GraphView(APIView):


    def get(self, request):
        return Response(build_graph(request.user))
