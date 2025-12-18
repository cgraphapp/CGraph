// android/app/src/main/kotlin/com/cgraph/NativeEncryption.kt
/**
 * Native encryption using Android Keystore
 */

package com.cgraph

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import java.security.KeyStore
import android.util.Base64

class NativeEncryption(private val context: Context) {
    
    private val keyStore: KeyStore by lazy {
        KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
    }
    
    fun generateKey(alias: String) {
        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
        )
        
        val keySpec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        ).apply {
            setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        }.build()
        
        keyGenerator.init(keySpec)
        keyGenerator.generateKey()
    }
    
    fun encryptMessage(message: String, alias: String): String {
        val key = keyStore.getKey(alias, null) as SecretKey
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key)
        
        val encryptedBytes = cipher.doFinal(message.toByteArray())
        val iv = cipher.iv
        
        // Combine IV + ciphertext
        val combined = iv + encryptedBytes
        return Base64.encodeToString(combined, Base64.DEFAULT)
    }
    
    fun decryptMessage(encryptedMessage: String, alias: String): String {
        val key = keyStore.getKey(alias, null) as SecretKey
        val combined = Base64.decode(encryptedMessage, Base64.DEFAULT)
        
        val iv = combined.sliceArray(0 until 12)
        val ciphertext = combined.sliceArray(12 until combined.size)
        
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val gcmSpec = GCMParameterSpec(128, iv)
        cipher.init(Cipher.DECRYPT_MODE, key, gcmSpec)
        
        val decrypted = cipher.doFinal(ciphertext)
        return String(decrypted)
    }
}
