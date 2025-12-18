// ios/Runner/NativeEncryption.swift
/**
 * Native encryption using iOS Keychain
 * Integration with Flutter layer
 */

import Foundation
import Security
import CryptoKit

@available(iOS 13.0, *)
class NativeEncryption {
    static let shared = NativeEncryption()
    
    // MARK: - Keychain Operations
    
    func savePrivateKey(_ key: String, forUser userId: String) throws {
        let keyData = key.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: userId,
            kSecAttrService as String: "cgraph.encryption",
            kSecValueData as String: keyData,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        // Delete existing key
        SecItemDelete(query as CFDictionary)
        
        // Add new key
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw NSError(domain: "Keychain", code: Int(status))
        }
    }
    
    func retrievePrivateKey(forUser userId: String) throws -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: userId,
            kSecAttrService as String: "cgraph.encryption",
            kSecReturnData as String: true
        ]
        
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        
        guard status == errSecSuccess else {
            if status == errSecItemNotFound {
                return nil
            }
            throw NSError(domain: "Keychain", code: Int(status))
        }
        
        guard let keyData = result as? Data else {
            throw NSError(domain: "Keychain", code: -1)
        }
        
        return String(data: keyData, encoding: .utf8)
    }
    
    // MARK: - Encryption
    
    @available(iOS 13.0, *)
    func encryptMessage(_ message: String, withKey key: String) throws -> String {
        let messageData = message.data(using: .utf8)!
        let keyData = key.data(using: .utf8)!
        
        let sealedBox = try AES.GCM.seal(messageData, using: SymmetricKey(data: keyData))
        
        // Combine nonce + ciphertext + tag
        var combined = Data()
        combined.append(sealedBox.nonce.withUnsafeBytes { Data($0) })
        combined.append(sealedBox.ciphertext)
        combined.append(sealedBox.tag)
        
        return combined.base64EncodedString()
    }
    
    @available(iOS 13.0, *)
    func decryptMessage(_ encryptedMessage: String, withKey key: String) throws -> String {
        let encryptedData = Data(base64Encoded: encryptedMessage)!
        let keyData = key.data(using: .utf8)!
        
        // Extract nonce (12 bytes)
        let nonce = try AES.GCM.Nonce(data: encryptedData.prefix(12))
        
        // Extract ciphertext and tag
        let combined = encryptedData.dropFirst(12)
        
        let sealedBox = try AES.GCM.SealedBox(nonce: nonce, ciphertext: combined.prefix(combined.count - 16), tag: combined.suffix(16))
        
        let decryptedData = try AES.GCM.open(sealedBox, using: SymmetricKey(data: keyData))
        
        return String(data: decryptedData, encoding: .utf8)!
    }
}
