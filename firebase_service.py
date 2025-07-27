import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from typing import Dict, List, Optional
import json
from datetime import datetime
import time

class FirebaseService:
    """Firebase authentication and database service"""
    
    def __init__(self):
        self.db = None
        self.initialized = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to get credentials from environment variable
                firebase_key = os.getenv('FIREBASE_KEY')
                
                if firebase_key:
                    # Parse JSON from environment variable
                    cred_dict = json.loads(firebase_key)
                    cred = credentials.Certificate(cred_dict)
                else:
                    # Fallback to service account file (for local development)
                    key_path = os.path.join(os.path.dirname(__file__), 'firebase_key.json')
                    if os.path.exists(key_path):
                        cred = credentials.Certificate(key_path)
                    else:
                        print("Warning: Firebase credentials not found. Using mock mode.")
                        self.initialized = False
                        return
                
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.initialized = True
            print("Firebase initialized successfully")
            
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self.initialized = False
    
    def verify_token(self, id_token: str) -> Optional[Dict]:
        """Verify Firebase ID token"""
        if not self.initialized:
            return None
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name', '')
            }
        except Exception as e:
            print(f"Token verification failed: {e}")
            return None
    
    def save_signal(self, user_id: str, signal_data: Dict, file_name: str = None) -> bool:
        """Save trading signal to Firestore"""
        if not self.initialized:
            return self._mock_save_signal(user_id, signal_data, file_name)
        
        try:
            signal_doc = {
                'user_id': user_id,
                'signal': signal_data,
                'file_name': file_name,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            # Add to signals collection
            doc_ref = self.db.collection('signals').add(signal_doc)
            
            # Update user's signal count
            user_ref = self.db.collection('users').document(user_id)
            user_ref.set({
                'last_signal': firestore.SERVER_TIMESTAMP,
                'total_signals': firestore.Increment(1)
            }, merge=True)
            
            return True
            
        except Exception as e:
            print(f"Error saving signal: {e}")
            return False
    
    def get_user_signals(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's trading signals from Firestore"""
        if not self.initialized:
            return self._mock_get_signals(user_id)
        
        try:
            signals_ref = self.db.collection('signals')
            query = signals_ref.where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            signals = []
            for doc in query.stream():
                signal_data = doc.to_dict()
                signal_data['id'] = doc.id
                signals.append(signal_data)
            
            return signals
            
        except Exception as e:
            print(f"Error getting signals: {e}")
            return []
    
    def save_feedback(self, user_id: str, signal_id: str, rating: int, comment: str = None) -> bool:
        """Save user feedback for a signal"""
        if not self.initialized:
            return True  # Mock success
        
        try:
            feedback_doc = {
                'user_id': user_id,
                'signal_id': signal_id,
                'rating': rating,
                'comment': comment,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.db.collection('feedback').add(feedback_doc)
            
            # Update signal with feedback
            if signal_id:
                signal_ref = self.db.collection('signals').document(signal_id)
                signal_ref.update({
                    'feedback_rating': rating,
                    'feedback_comment': comment,
                    'feedback_timestamp': firestore.SERVER_TIMESTAMP
                })
            
            return True
            
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user trading statistics"""
        if not self.initialized:
            return self._mock_user_stats()
        
        try:
            # Get user signals
            signals = self.get_user_signals(user_id, limit=100)
            
            total_signals = len(signals)
            wins = sum(1 for s in signals if s.get('signal', {}).get('outcome') == 'WIN')
            losses = sum(1 for s in signals if s.get('signal', {}).get('outcome') == 'LOSS')
            
            win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
            
            # Calculate PnL (mock for now)
            total_pnl = sum(float(s.get('signal', {}).get('pnl', '0').replace('+', '').replace('%', '')) 
                          for s in signals if s.get('signal', {}).get('pnl'))
            
            return {
                'total_signals': total_signals,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 1),
                'total_pnl': round(total_pnl, 2),
                'avg_confidence': 78.5,  # Mock
                'best_timeframe': '1h'   # Mock
            }
            
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return self._mock_user_stats()
    
    def _mock_save_signal(self, user_id: str, signal_data: Dict, file_name: str = None) -> bool:
        """Mock signal saving when Firebase is not available"""
        print(f"Mock: Saved signal for user {user_id}")
        return True
    
    def _mock_get_signals(self, user_id: str) -> List[Dict]:
        """Mock signal retrieval when Firebase is not available"""
        return [
            {
                'id': 'mock_signal_1',
                'signal': {
                    'action': 'BUY',
                    'entry': 1950.50,
                    'take_profit': 1980.00,
                    'stop_loss': 1920.00,
                    'confidence': '85%',
                    'timeframe': '1h'
                },
                'created_at': '2024-01-15T10:30:00Z',
                'file_name': 'XAUUSD_chart.png'
            },
            {
                'id': 'mock_signal_2',
                'signal': {
                    'action': 'SELL',
                    'entry': 1975.25,
                    'take_profit': 1945.00,
                    'stop_loss': 2005.00,
                    'confidence': '78%',
                    'timeframe': '4h'
                },
                'created_at': '2024-01-16T14:15:00Z',
                'file_name': 'EURUSD_data.csv'
            }
        ]
    
    def _mock_user_stats(self) -> Dict:
        """Mock user statistics when Firebase is not available"""
        return {
            'total_signals': 25,
            'wins': 17,
            'losses': 8,
            'win_rate': 68.0,
            'total_pnl': 245.75,
            'avg_confidence': 78.5,
            'best_timeframe': '1h'
        }
