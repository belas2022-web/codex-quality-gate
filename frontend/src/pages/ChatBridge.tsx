import { fetchChats } from '../api/client';
import ChatActivityPanel from '../components/ChatActivityPanel';
import ResourcePage from './ResourcePage';

export default function ChatBridge() {
  return (
    <ResourcePage
      title="Chat Bridge"
      load={fetchChats}
      render={(chats) => <ChatActivityPanel chats={chats} />}
    />
  );
}
