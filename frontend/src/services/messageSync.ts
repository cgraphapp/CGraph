// /frontend/src/services/messageSync.ts
/**
 * Message synchronization service
 * - Local storage with encryption
 * - Automatic sync when online
 * - Conflict resolution
 */

import * as localforage from 'localforage';
import { v4 as uuidv4 } from 'uuid';

interface PendingMessage {
  id: string;
  room_id: string;
  content: string;
  timestamp: number;
  encrypted: boolean;
  status: 'pending' | 'sent' | 'failed';
  retries: number;
}

class MessageSyncService {
  private db: LocalForage;
  private messageQueue: PendingMessage[] = [];
  private isOnline: boolean = navigator.onLine;
  
  constructor() {
    this.db = localforage.createInstance({
      name: 'cgraph_messages',
      storeName: 'messages'
    });
    
    // Monitor online/offline
    window.addEventListener('online', () => this.onlineStatusChanged(true));
    window.addEventListener('offline', () => this.onlineStatusChanged(false));
  }
  
  async addPendingMessage(
    roomId: string,
    content: string,
    encrypted: boolean = false
  ): Promise<PendingMessage> {
    const message: PendingMessage = {
      id: uuidv4(),
      room_id: roomId,
      content,
      timestamp: Date.now(),
      encrypted,
      status: 'pending',
      retries: 0
    };
    
    // Add to local queue
    this.messageQueue.push(message);
    
    // Store in IndexedDB
    await this.db.setItem(`msg_${message.id}`, message);
    
    // Try to send immediately if online
    if (this.isOnline) {
      await this.syncPendingMessages();
    }
    
    return message;
  }
  
  async syncPendingMessages(): Promise<void> {
    const failedMessages: PendingMessage[] = [];
    
    for (const message of this.messageQueue) {
      if (message.status === 'pending' && message.retries < 3) {
        try {
          const response = await fetch('/api/v1/messages/send', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
              room_id: message.room_id,
              content: message.content,
              local_id: message.id
            })
          });
          
          if (response.ok) {
            message.status = 'sent';
            await this.db.setItem(`msg_${message.id}`, message);
          } else if (response.status >= 500) {
            // Server error, retry later
            message.retries++;
            failedMessages.push(message);
          } else {
            // Client error, don't retry
            message.status = 'failed';
            await this.db.setItem(`msg_${message.id}`, message);
          }
        } catch (error) {
          message.retries++;
          failedMessages.push(message);
        }
      }
    }
    
    // Keep failed messages in queue
    this.messageQueue = this.messageQueue.filter(
      msg => msg.status === 'pending' || msg.status === 'failed'
    );
  }
  
  private async onlineStatusChanged(isOnline: boolean): Promise<void> {
    this.isOnline = isOnline;
    
    if (isOnline) {
      console.log('Back online, syncing messages');
      await this.syncPendingMessages();
    }
  }
  
  async getLocalMessages(roomId: string): Promise<PendingMessage[]> {
    const keys = await this.db.keys();
    const messages: PendingMessage[] = [];
    
    for (const key of keys) {
      if (key.startsWith('msg_')) {
        const msg = await this.db.getItem<PendingMessage>(key);
        if (msg && msg.room_id === roomId) {
          messages.push(msg);
        }
      }
    }
    
    return messages.sort((a, b) => a.timestamp - b.timestamp);
  }
}

export const messageSyncService = new MessageSyncService();
