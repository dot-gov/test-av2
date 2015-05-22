package com.accati.wifichangestatus;

import android.app.Activity;
import android.content.Context;
import android.net.wifi.WifiConfiguration;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.util.Log;

import java.util.List;

public class MainActivity extends Activity {

	@Override

    /**
     * Possible intents:
     *
     * No extra param = does nothing
     *
     * "SSID" e "psk" -> connects to specified network, also removing any net configuration. THIS ALWAYS ENABLES THE WIFI! NB: this uses some special WPA settings!
     * "wifi"="info" -> get net info
     * "wifi"="disable" -> disables network, also removing any net configuration
     *
     * The wifi options has precedence over SSID and psk (so if you specify both, only wifi is used)
     */

	public void onCreate(Bundle savedInstanceState) {
        Log.i("WifiManager", "Starting Wifimanager");
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		WifiManager wfm = (WifiManager) getSystemService(Context.WIFI_SERVICE);
        Log.i("WifiManager", "Getting intents");

        String wifi = getIntent().getStringExtra("wifi");
        String SSID = getIntent().getStringExtra("SSID");
        String psk = getIntent().getStringExtra("psk");

        //Some hard coded values used for testing
        //disable = Boolean.TRUE;
        //String SSID = "RSSM";//= getIntent().getStringExtra("SSID");
        //String psk = "SteveJobsSux!";//= getIntent().getStringExtra("psk");
        //SSID = "TP-LINK_9EF638";//= getIntent().getStringExtra("SSID");
        //psk = "wroadoaqle38lechlesw";//= getIntent().getStringExtra("psk");

        //Deprecated
		//boolean sw = false;

        String ret = "";
        Log.i("WifiManager", "Starting try");
		try {

            if ("disable".equalsIgnoreCase(wifi))
            {
                removeAllNetworks(wfm);
                wfm.setWifiEnabled(Boolean.FALSE);
            }
            else if ("info".equalsIgnoreCase(wifi))
            {
                Log.i("WifiManager", "info");
                ret = wfm.getConnectionInfo().getSSID();
            }
            else if  (SSID != null && psk != null)
            {
                Log.i("WifiManager", "ssid = " + SSID + " pks = " + psk);

                removeAllNetworks(wfm);


                //Create new WPA configuration
                WifiConfiguration wifiConfig = new WifiConfiguration();
                wifiConfig.SSID = "\"" + SSID + "\"";
                wifiConfig.preSharedKey = "\"" + psk + "\"";
                wifiConfig.allowedProtocols.set(WifiConfiguration.Protocol.WPA);
                wifiConfig.allowedProtocols.set(WifiConfiguration.Protocol.RSN);
                wifiConfig.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.WPA_PSK);
                wifiConfig.allowedPairwiseCiphers.set(WifiConfiguration.PairwiseCipher.TKIP);
                wifiConfig.allowedPairwiseCiphers.set(WifiConfiguration.PairwiseCipher.CCMP);
                wifiConfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.TKIP);
                wifiConfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.CCMP);
                wifiConfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.WEP40);
                wifiConfig.allowedGroupCiphers.set(WifiConfiguration.GroupCipher.WEP104);

                wifiConfig.priority = 1;
                //wifiConfig.status = WifiConfiguration.Status.ENABLED;
                int netId = wfm.addNetwork(wifiConfig);
                wfm.enableNetwork(netId, true);
                wfm.saveConfiguration();

                Log.i("WifiManager", "Config saved");

                //Wait for wifi enabled
                do {
                    wfm.setWifiEnabled(true);
                    wfm.reconnect();
                    Thread.sleep(100);
                    Log.i("WifiManager", "waiting until wifi is enabled");
                }while (WifiManager.WIFI_STATE_ENABLED != wfm.getWifiState());

                Log.i("WifiManager", "Config number = " + wfm.getConfiguredNetworks().size());

                //Prints the only one config just added
                WifiConfiguration checkConfig = wfm.getConfiguredNetworks().get(0);
                Log.i("WifiManager", "Config 0 SSID =" + checkConfig.SSID);

                //Check if connected to the right network
                // This assumes that the SSID can decoded to UTF-8
                while (wfm.getConnectionInfo().getSSID() == null || !SSID.equals(wfm.getConnectionInfo().getSSID())){
                    Thread.sleep(100);
                    Log.i("WifiManager", "Waiting to complete connection...");
                    Log.i("WifiManager", "SSID attuale = " + wfm.getConnectionInfo().getSSID());
                    Log.i("WifiManager", "SSID richiesto = " + SSID);
                }
                Log.i("WifiManager", "Connected to = " + wfm.getConnectionInfo().getSSID());

            }
            /*  This code is deprecated. Now enable does not exist. Disable also removes any net configuration*/
            /*
			else if (wifi != null)
                {
                    Log.i("WifiManager", "wifi = " + wifi);
                    if ("true".equalsIgnoreCase(wifi) || "false".equalsIgnoreCase(wifi)) {
                        sw = Boolean.parseBoolean(wifi);
                        ret = Boolean.toString(wfm.setWifiEnabled(sw));
                    }
                }
            */
            else
                {
                    //Does nothing
                    Log.i("WifiManager", "no params - does nothing");
                    //ret = Boolean.toString(wfm.setWifiEnabled(sw));
                }
		} catch (Exception e) {
            e.printStackTrace();
            Log.e("WifiManagerStackTrace", "Exception occurred! Disabling wifi.");
            ret = Boolean.toString(wfm.setWifiEnabled(false));
		}
        System.out.println(ret);
        Log.i("WifiManager", ret);

        System.exit(0);
	}

    private void removeAllNetworks(WifiManager wfm) throws InterruptedException {

        //to list wifi configured networks I need wifi on
        List<WifiConfiguration> wifiList = wfm.getConfiguredNetworks();
        //I need to enable network in order to
        wfm.setWifiEnabled(true);
        int maxIteratione = 100;
        while (wifiList == null && maxIteratione > 1){
            Log.i("WifiManager", "waiting 100 ms until wifi list is not null");
            Thread.sleep(100);
            wifiList = wfm.getConfiguredNetworks();
            maxIteratione --;
        }

        for (WifiConfiguration netw : wifiList)
        {
            wfm.removeNetwork(netw.networkId);
        }
        wfm.saveConfiguration();

        Log.i("WifiManager", "removed configs");
    }
}