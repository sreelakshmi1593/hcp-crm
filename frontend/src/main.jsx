import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { store } from './store'
import LogInteractionScreen from './pages/LogInteractionScreen'

ReactDOM.createRoot(document.getElementById('root')).render(
  <Provider store={store}>
    <LogInteractionScreen />
  </Provider>
)
