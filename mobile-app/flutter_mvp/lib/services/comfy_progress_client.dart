import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:web_socket_channel/web_socket_channel.dart';

class ComfyProgressClient {
  ComfyProgressClient({required String baseUrl})
      : baseUri = Uri.parse(_normalizeBaseUrl(baseUrl)),
        clientId = _makeClientId();

  final Uri baseUri;
  final String clientId;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;

  final StreamController<ComfyProgressEvent> _events = StreamController<ComfyProgressEvent>.broadcast();

  Stream<ComfyProgressEvent> get events => _events.stream;

  static String _normalizeBaseUrl(String value) {
    return value.endsWith('/') ? value.substring(0, value.length - 1) : value;
  }

  static String _joinPaths(String basePath, String childPath) {
    final left = basePath.endsWith('/') ? basePath.substring(0, basePath.length - 1) : basePath;
    final right = childPath.startsWith('/') ? childPath.substring(1) : childPath;
    if (left.isEmpty || left == '/') return '/$right';
    return '$left/$right';
  }

  static String _makeClientId() {
    final random = Random().nextInt(0xFFFFFF).toRadixString(16);
    return 'mobile_${DateTime.now().millisecondsSinceEpoch}_$random';
  }

  Uri get websocketUri {
    final scheme = baseUri.scheme == 'https' ? 'wss' : 'ws';
    return baseUri.replace(
      scheme: scheme,
      path: _joinPaths(baseUri.path, '/ws'),
      queryParameters: {'clientId': clientId},
    );
  }

  void connect() {
    close();
    _channel = WebSocketChannel.connect(websocketUri);
    _events.add(ComfyProgressEvent(type: 'socket_open', message: 'WebSocket connecting'));
    _subscription = _channel!.stream.listen(
      _handleMessage,
      onError: (error) {
        _events.add(ComfyProgressEvent(type: 'socket_error', message: error.toString()));
      },
      onDone: () {
        _events.add(ComfyProgressEvent(type: 'socket_close', message: 'WebSocket closed'));
      },
    );
  }

  void _handleMessage(dynamic message) {
    if (message is! String) return;
    try {
      final decoded = jsonDecode(message);
      if (decoded is Map<String, dynamic>) {
        _events.add(ComfyProgressEvent.fromJson(decoded));
      }
    } catch (_) {
      // Ignore non-json websocket messages.
    }
  }

  Future<void> close() async {
    await _subscription?.cancel();
    _subscription = null;
    await _channel?.sink.close();
    _channel = null;
  }

  Future<void> dispose() async {
    await close();
    await _events.close();
  }
}

class ComfyProgressEvent {
  const ComfyProgressEvent({
    required this.type,
    this.data,
    this.message,
  });

  final String type;
  final Map<String, dynamic>? data;
  final String? message;

  factory ComfyProgressEvent.fromJson(Map<String, dynamic> json) {
    final rawData = json['data'];
    return ComfyProgressEvent(
      type: json['type'] as String? ?? 'unknown',
      data: rawData is Map<String, dynamic> ? rawData : null,
      message: json['message'] as String?,
    );
  }

  bool get isProgress => type == 'progress';
  bool get isExecuting => type == 'executing';
  bool get isExecutionError => type == 'execution_error';

  int? get progressValue => data?['value'] is int ? data!['value'] as int : null;
  int? get progressMax => data?['max'] is int ? data!['max'] as int : null;
  String? get executingNode => data?['node']?.toString();
}
