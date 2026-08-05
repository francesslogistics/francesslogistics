from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from .models import AppSettings, Inquiry, InquiryFile
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from .serializers import AppSettingsSerializer, InquirySerializer


class AppSettingsView(generics.RetrieveUpdateAPIView):
    """GET/PATCH/PUT the single global settings row."""
    serializer_class = AppSettingsSerializer

    def get_object(self):
        return AppSettings.load()


class InquiryViewSet(viewsets.ModelViewSet):
    """Public 'Request a Quote' submissions (quote.html POSTs here with no
    auth, as multipart/form-data since it includes file uploads for
    questions 10.5 and 13), listed/triaged by staff on the Inquiries nav
    (auth required for everything except creating a new one)."""
    queryset = Inquiry.objects.all().prefetch_related("files")
    serializer_class = InquirySerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        inquiry = serializer.save()
        for f in self.request.FILES.getlist("dgAttachments"):
            InquiryFile.objects.create(inquiry=inquiry, kind=InquiryFile.Kind.DG_DOC, file=f)
        for f in self.request.FILES.getlist("attachments"):
            InquiryFile.objects.create(inquiry=inquiry, kind=InquiryFile.Kind.PROOF, file=f)


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok", "service": "francess-logistics-backend"})

@ensure_csrf_cookie
def dashboard_view(request):
    # Forces the csrftoken cookie to be set on first load, so the front-end's
    # fetch() calls always have a token available to send back on POST/PATCH/
    # DELETE — without this, a stale session cookie (e.g. from /admin/) makes
    # DRF's SessionAuthentication demand a CSRF header the page never sends,
    # which surfaces as a 403 on things like /api/accounts/login/.
    return render(request, 'core/dashboard.html')


def client_index_view(request):
    """Public marketing site — served at '/' (and '/index.html' so the
    relative links inside the page keep working, e.g. href="index.html")."""
    return render(request, 'core/site/index.html')


def client_quote_view(request):
    """Public 'Request a Quote' page — served at '/quote.html'."""
    return render(request, 'core/site/quote.html')
