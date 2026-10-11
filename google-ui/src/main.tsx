import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import NativeStudio from './NativeStudio';
import './index.css';

const native = new URLSearchParams(window.location.search).get('native') === '1';
createRoot(document.getElementById('root')!).render(native ? <NativeStudio /> : <App />);
