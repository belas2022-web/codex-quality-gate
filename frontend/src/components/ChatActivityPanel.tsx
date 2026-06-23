import type { ChatConnector } from '../api/client';

type Props = {
  chats?: ChatConnector[] | null;
};

export default function ChatActivityPanel({ chats }: Props) {
  const rows = chats ?? [];
  return (
    <article className="panel">
      <h2>Chat bridge permissions</h2>
      <div className="permission-stack">
        {rows.length === 0 ? (
          <span>No chat connectors configured.</span>
        ) : (
          rows.map((chat) => (
            <span key={chat.name}>
              {chat.name}: {chat.enabled ? 'available' : 'disabled'}, {chat.status}, read{' '}
              {chat.allowed_read_count}, write {chat.allowed_write_count}
            </span>
          ))
        )}
      </div>
    </article>
  );
}
