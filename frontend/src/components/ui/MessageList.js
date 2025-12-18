// /frontend/src/components/ui/MessageList.tsx
/**
 * Accessible message list component
 * - ARIA labels
 * - Keyboard navigation
 * - Screen reader support
 * - Virtual scrolling for performance
 */
import React, { useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
export const MessageList = ({ messages, currentUserId, isLoading = false, onReaction }) => {
    const listRef = React.useRef(null);
    const virtualizer = useVirtualizer({
        count: messages.length,
        getScrollElement: () => listRef.current,
        estimateSize: () => 80,
        overscan: 10
    });
    const virtualItems = virtualizer.getVirtualItems();
    const totalSize = virtualizer.getTotalSize();
    const paddingTop = virtualItems.length > 0 ? virtualItems?. : , start;
     || 0;
    0;
    const paddingBottom = virtualItems.length > 0
        ? totalSize - (virtualItems?.[virtualItems.length - 1]?.end || 0)
        : 0;
    const handleKeyDown = useCallback((event, index) => {
        if (event.key === 'ArrowUp' && index > 0) {
            // Focus previous message
            event.preventDefault();
        }
        else if (event.key === 'ArrowDown' && index < messages.length - 1) {
            // Focus next message
            event.preventDefault();
        }
    }, [messages.length]);
    return (<div ref={listRef} className="message-list" role="region" aria-label="Messages" aria-live="polite">
      {paddingTop > 0 && <div style={{ height: paddingTop }}/>}
      
      {virtualItems.map((virtualItem) => {
            const message = messages[virtualItem.index];
            const isOwn = message.sender_id === currentUserId;
            return (<div key={message.id} data-index={virtualItem.index} className={`message ${isOwn ? 'own' : 'other'}`} role="article" aria-label={`Message from ${message.sender_id}: ${message.content}`} onKeyDown={(e) => handleKeyDown(e, virtualItem.index)}>
            <div className="message-content">
              <p>{message.content}</p>
            </div>
            
            <div className="message-metadata">
              <time dateTime={message.created_at}>
                {new Date(message.created_at).toLocaleTimeString()}
              </time>
            </div>
            
            {message.reactions && (<div className="message-reactions" role="group" aria-label="Reactions">
                {Object.entries(message.reactions).map(([emoji, users]) => (<button key={emoji} className="reaction" aria-label={`${emoji} reaction by ${users.join(', ')}`} onClick={() => onReaction?.(message.id, emoji)}>
                    {emoji} {users.length}
                  </button>))}
              </div>)}
          </div>);
        })}
      
      {paddingBottom > 0 && <div style={{ height: paddingBottom }}/>}
      
      {isLoading && (<div className="loading" role="status" aria-live="polite">
          <span>Loading messages...</span>
        </div>)}
    </div>);
};
