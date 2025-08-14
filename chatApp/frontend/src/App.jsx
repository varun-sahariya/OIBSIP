import React, { useState, useEffect, useReducer, useRef } from 'react';
import io from 'socket.io-client';

const socket = io('http://localhost:5000');

// The reducer is perfect. No changes needed.
const initialState = { chats: { public: [] }, onlineUsers: [] };
function chatReducer(state, action) {
    switch (action.type) {
        case 'SET_CHAT_HISTORY': {
            const { room, history } = action.payload;
            return { ...state, chats: { ...state.chats, [room]: history } };
        }
        case 'ADD_MESSAGE': {
            const { room, message } = action.payload;
            return { ...state, chats: { ...state.chats, [room]: [...(state.chats[room] || []), message] } };
        }
        case 'CLEAR_CHAT': {
            const { room } = action.payload;
            return { ...state, chats: { ...state.chats, [room]: [] } };
        }
        case 'SET_ONLINE_USERS': {
            return { ...state, onlineUsers: action.payload };
        }
        case 'ADD_CHAT_ROOM': {
            const { room } = action.payload;
            if (state.chats[room]) return state;
            return { ...state, chats: { ...state.chats, [room]: [] } };
        }
        default:
            return state;
    }
}

// --- Message Component with new animations and styles ---
const Message = ({ message }) => {
    const isMe = message.sender === 'me';

    // File Message
    if (message.type === 'file') {
        return (
            <div className={`flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300 ${isMe ? 'items-end' : 'items-start'}`}>
                <div className="max-w-xs md:max-w-md">
                    <div className="p-2 rounded-lg bg-black/20">
                        {/* NEW: Display username inside the bubble */}
                        {!isMe && <p className="font-bold text-indigo-400 text-sm mb-2 px-1">{message.user}</p>}
                        {message.file_type.startsWith('image/') ? (
                            <img src={message.file_url} alt={message.filename} className="max-w-xs rounded-md" />
                        ) : message.file_type.startsWith('audio/') ? (
                            <audio controls src={message.file_url} className="w-full"></audio>
                        ) : (
                            <div className="p-2 bg-slate-800/50 rounded-lg flex items-center gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-slate-400"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
                                <a href={message.file_url} target="_blank" rel="noopener noreferrer" download className="text-indigo-400 hover:underline truncate">{message.filename}</a>
                            </div>
                        )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 px-2">{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                </div>
            </div>
        );
    }

    // Text Message
    return (
        <div className={`flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300 ${isMe ? 'items-end' : 'items-start'}`}>
            <div className="max-w-md">
                <div className={`px-4 py-2 rounded-2xl ${isMe ? 'bg-indigo-500 text-white rounded-br-lg' : 'bg-slate-700 text-slate-200 rounded-bl-lg'}`}>
                    {/* NEW: Display username inside the bubble */}
                    {!isMe && <p className="font-bold text-indigo-400 text-sm mb-1">{message.user}</p>}
                    <p className="whitespace-pre-wrap break-words">{message.text}</p>
                </div>
                <p className="text-xs text-slate-500 mt-1 px-2">{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
        </div>
    );
};


function App() {
    // All state and handlers are the same.
    const [username, setUsername] = useState('');
    const [hasJoined, setHasJoined] = useState(false);
    const [activeRoom, setActiveRoom] = useState('public');
    const [newMessage, setNewMessage] = useState('');
    const [state, dispatch] = useReducer(chatReducer, initialState);
    const { chats, onlineUsers } = state;
    const fileInputRef = useRef(null);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [chats, activeRoom]);

    useEffect(() => {
        const onChatHistory = (data) => dispatch({ type: 'SET_CHAT_HISTORY', payload: data });
        const onChatCleared = (data) => dispatch({ type: 'CLEAR_CHAT', payload: data });
        const onPublicMessage = (data) => dispatch({ type: 'ADD_MESSAGE', payload: { room: 'public', message: { ...data, sender: 'them' } } });
        const onPrivateMessage = (data) => dispatch({ type: 'ADD_MESSAGE', payload: { room: data.room, message: { ...data.message, sender: 'them' } } });
        const onPrivateChatStarted = (data) => {
            dispatch({ type: 'ADD_CHAT_ROOM', payload: data });
            setActiveRoom(data.room);
        };
        const onUpdateUserList = (users) => dispatch({ type: 'SET_ONLINE_USERS', payload: users.filter(u => u !== username) });
        const onAiResponse = (ai_message_data) => dispatch({ type: 'ADD_MESSAGE', payload: { room: 'public', message: ai_message_data } });
        const onFileShared = (data) => {
            const room = data.room || 'public';
            const message = data.message || data;
            dispatch({ type: 'ADD_MESSAGE', payload: { room, message: { ...message, sender: 'them', type: 'file' } } });
        };

        socket.on('chat_history', onChatHistory);
        socket.on('chat_cleared', onChatCleared);
        socket.on('message', onPublicMessage);
        socket.on('private_message', onPrivateMessage);
        socket.on('private_chat_started', onPrivateChatStarted);
        socket.on('update_user_list', onUpdateUserList);
        socket.on('ai_response', onAiResponse);
        socket.on('file_shared', onFileShared);

        return () => {
            socket.off('chat_history'); socket.off('chat_cleared'); socket.off('message'); socket.off('private_message');
            socket.off('private_chat_started'); socket.off('update_user_list'); socket.off('ai_response'); socket.off('file_shared');
        };
    }, [username]);
    const handleJoin = (e) => { e.preventDefault(); if (username.trim()) { setHasJoined(true); socket.emit('user_joined', username); }};
    const startPrivateChat = (targetUser) => { socket.emit('start_private_chat', targetUser); };
    const handleClearChat = (roomName) => {
        if (window.confirm(`Are you sure you want to clear the history for this chat? This cannot be undone.`)) {
            dispatch({ type: 'CLEAR_CHAT', payload: { room: roomName } });
            socket.emit('clear_chat', roomName);
        }
    };
    const handleSendMessage = (e) => {
        e.preventDefault();
        const messageText = newMessage.trim();

        if (messageText.startsWith('/ai ')) {
            const prompt = messageText.substring(4);
            if (prompt) {
                const promptMessage = { user: username, text: messageText, sender: 'me', timestamp: new Date().toISOString() };
                dispatch({ type: 'ADD_MESSAGE', payload: { room: 'public', message: promptMessage } });
                socket.emit('ai_message', prompt);
            }
        } else if (messageText) {
            const messageData = { user: username, text: messageText, sender: 'me', timestamp: new Date().toISOString() };
            dispatch({ type: 'ADD_MESSAGE', payload: { room: activeRoom, message: messageData } });
            if (activeRoom === 'public') {
                socket.emit('message', { user: username, text: messageText });
            } else {
                socket.emit('private_message', { room: activeRoom, message: { user: username, text: messageText } });
            }
        }
        setNewMessage('');
    };
    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('sender', username);
        formData.append('room', activeRoom);
        try {
            const response = await fetch('http://localhost:5000/upload', { method: 'POST', body: formData });
            if (response.ok) {
                const fileMessageData = { user: username, file_url: URL.createObjectURL(file), filename: file.name, file_type: file.type, sender: 'me', type: 'file', timestamp: new Date().toISOString() };
                dispatch({ type: 'ADD_MESSAGE', payload: { room: activeRoom, message: fileMessageData } });
            }
        } catch (error) { console.error('Error uploading file:', error); }
    };

    // --- UI Rendering ---
    if (!hasJoined) { 
        return ( 
            <div className="h-screen bg-slate-900 flex justify-center items-center p-4">
                <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 p-8 rounded-2xl shadow-2xl w-full max-w-sm animate-in fade-in duration-500">
                    <h1 className="text-3xl font-bold text-white text-center mb-6">Welcome to <span className="text-indigo-400">Chat App</span></h1>
                    <form onSubmit={handleJoin} className="space-y-4">
                        <input type="text" placeholder="Enter your username" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full bg-slate-700/50 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all duration-300"/>
                        <button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-500 rounded-lg py-3 font-semibold text-white transition-colors shadow-lg shadow-indigo-600/20">Join Chat</button>
                    </form>
                </div>
            </div> 
        ); 
    }
    
    return (
        <div className="h-screen w-full bg-gradient-to-br from-gray-900 via-slate-900 to-black text-slate-200 font-sans overflow-hidden">
            <div className="flex h-full p-4 gap-4">
                <aside className="w-64 bg-black/20 backdrop-blur-md border border-slate-700/50 rounded-2xl p-4 flex flex-col">
                    <h2 className="text-lg font-bold mb-4 text-white">Online Users ({onlineUsers.length})</h2>
                    <ul className="space-y-2 overflow-y-auto pr-2">
                        {onlineUsers.map((user) => (
                            <li key={user}>
                                <button onClick={() => startPrivateChat(user)} className="w-full text-left hover:bg-white/10 p-2 rounded-lg transition-colors flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-green-500 flex-shrink-0"></div>
                                    <span className="truncate font-medium">{user}</span>
                                </button>
                            </li>
                        ))}
                    </ul>
                </aside>

                <div className="flex-1 flex flex-col bg-black/20 backdrop-blur-md border border-slate-700/50 rounded-2xl">
                    <header className="p-4 border-b border-slate-700/50 flex justify-between items-center">
                        <div className="flex space-x-2 overflow-x-auto">
                            {Object.keys(chats).map(room => (
                                <button key={room} onClick={() => setActiveRoom(room)} className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${activeRoom === room ? 'bg-indigo-600 text-white' : 'bg-white/5 hover:bg-white/10'}`}>
                                    {room === 'public' ? 'Public Chat' : room.replace(username, '').replace('-', '')}
                                </button>
                            ))}
                        </div>
                        <button onClick={() => handleClearChat(activeRoom)} title="Clear chat history" className="p-2 text-slate-400 hover:text-red-500 rounded-full hover:bg-white/10 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" /></svg>
                        </button>
                    </header>
                    <main className="flex-1 p-6 overflow-y-auto">
                        <div className="space-y-6">
                            {chats[activeRoom]?.map((message, index) => (
                                <Message key={message.timestamp + index} message={message} />
                            ))}
                            <div ref={chatEndRef} />
                        </div>
                    </main>
                    <footer className="p-4 border-t border-slate-700/50">
                        <form onSubmit={handleSendMessage} className="flex items-center gap-4">
                            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden"/>
                            <button type="button" onClick={() => fileInputRef.current.click()} className="p-2 text-slate-400 hover:text-white transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.41-7.81 7.81a1.5 1.5 0 0 0 2.122 2.122l7.81-7.81" /></svg>
                            </button>
                            <input type="text" placeholder={`Message ${activeRoom === 'public' ? '#public' : onlineUsers.find(u => activeRoom.includes(u)) || ''}`} value={newMessage} onChange={(e) => setNewMessage(e.target.value)} className="flex-1 bg-slate-700/50 rounded-lg px-5 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all duration-300"/>
                            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 rounded-lg p-3 transition-colors text-white shadow-lg shadow-indigo-600/20">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6"><path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" /></svg>
                            </button>
                        </form>
                    </footer>
                </div>
            </div>
        </div>
    );
}

export default App;
