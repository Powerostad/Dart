from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q
from .models import Blog
from .serializers import BlogSerializer

class BlogCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BlogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlogListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        blogs = Blog.objects.filter(status='approved')
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)


class BlogSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        blogs = Blog.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            status='approved'
        )
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)


class BlogUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk, author=request.user)
        except Blog.DoesNotExist:
            return Response({"error": "Blog not found or you do not have permission to edit this blog."}, 
                            status=status.HTTP_404_NOT_FOUND)

        serializer = BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlogDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk, author=request.user)
            blog.delete()
            return Response({"message": "Blog deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Blog.DoesNotExist:
            return Response({"error": "Blog not found or you do not have permission to delete this blog."}, 
                            status=status.HTTP_404_NOT_FOUND)


class UserBlogsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blogs = Blog.objects.filter(author=request.user)
        serializer = BlogSerializer(blogs, many=True)
        return Response(serializer.data)

# Create your views here.
